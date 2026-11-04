// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IAgentVault} from "../src/IAgentVault.sol";
import {IAgentEscrow} from "../src/IAgentEscrow.sol";
import {AgentVault} from "../src/AgentVault.sol";
import {AgentEscrow} from "../src/AgentEscrow.sol";
import {ReentrancyGuard} from "../src/ReentrancyGuard.sol";
import {MockUSDC} from "./MockUSDC.sol";

/// @notice Non-standard ERC20 (USDT-style) that returns no boolean data on transfer/approve/transferFrom.
contract MockNonStandardERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function transfer(address to, uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "insufficient");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external {
        allowance[msg.sender][spender] = amount;
    }

    function transferFrom(address from, address to, uint256 amount) external {
        require(balanceOf[from] >= amount, "insufficient");
        require(allowance[from][msg.sender] >= amount, "allowance");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
    }
}

/// @notice Malicious ERC20 that attempts a reentrant call into AgentVault during transfer.
contract MockReentrantERC20 {
    mapping(address => uint256) public balanceOf;
    AgentVault public targetVault;
    address public attackerPayee;
    bool public attackArmed;
    bool public attackRefund;

    function setAttack(AgentVault _vault, address _payee, bool _armed) external {
        targetVault = _vault;
        attackerPayee = _payee;
        attackArmed = _armed;
        attackRefund = false;
    }

    function setAttackRefund(AgentVault _vault, bool _armed) external {
        targetVault = _vault;
        attackRefund = _armed;
        attackArmed = false;
    }

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        if (attackArmed) {
            targetVault.spendDirect(attackerPayee, 1_000);
        }
        if (attackRefund) {
            targetVault.onEscrowRefunded(1, 1_000);
        }
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function approve(address, uint256) external pure returns (bool) {
        return true;
    }

    function transferFrom(address, address, uint256) external pure returns (bool) {
        return true;
    }
}

interface Vm {
    function prank(address msgSender) external;
    function warp(uint256 newTimestamp) external;
    function expectRevert(bytes calldata revertData) external;
    function expectRevert(bytes4 revertSelector) external;
}

contract AgentEscrowVaultTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    MockUSDC private usdc;
    AgentVault private vault;
    AgentEscrow private escrow;

    address private owner = address(this);
    address private agentSessionKey = address(0xA11CE);
    address private whitelistedMerchant = address(0xB0B);
    address private unwhitelistedMerchant = address(0xBAD);
    address private providerA = address(0xCAFE);
    address private providerB = address(0xBEEF);
    address private evaluator = address(0xEA1);
    address private attacker = address(0xDEAD);

    uint256 private constant DEFAULT_DIRECT_CAP = 10_000;   // 0.01 USDC (6 decimals)
    uint256 private constant DEFAULT_ESCROW_CAP = 60_000;   // 0.06 USDC
    uint256 private constant DEFAULT_DAILY_CAP  = 100_000;  // 0.10 USDC
    uint256 private constant INITIAL_VAULT_USDC = 500_000;  // 0.50 USDC

    function setUp() public {
        vm.warp(1_700_000_000);
        usdc = new MockUSDC();
        vault = new AgentVault(address(usdc), agentSessionKey);
        escrow = new AgentEscrow(address(usdc));

        vault.setPayeeWhitelist(whitelistedMerchant, true);
        vault.setEscrowApproved(address(escrow), true);

        usdc.mint(address(vault), INITIAL_VAULT_USDC);
    }

    function _assertEqUint(uint256 a, uint256 b, string memory err) internal pure {
        require(a == b, err);
    }

    function _assertEqAddr(address a, address b, string memory err) internal pure {
        require(a == b, err);
    }

    function _assertEqBool(bool a, bool b, string memory err) internal pure {
        require(a == b, err);
    }

    function _assertEqBytes32(bytes32 a, bytes32 b, string memory err) internal pure {
        require(a == b, err);
    }

    function _assertEqStr(string memory a, string memory b, string memory err) internal pure {
        require(keccak256(bytes(a)) == keccak256(bytes(b)), err);
    }

    // =========================================================================
    // Vault Unit Tests (Case-V01 ~ Case-V05)
    // =========================================================================

    /// @notice Case-V01: Non-Owner attempting to call configureLimits, withdraw, pause, etc. must revert.
    function test_Case_V01_OnlyOwnerManagementAndEmergencyWithdraw() public {
        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.configureLimits(20_000, 80_000, 200_000);

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.withdraw(10_000);

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.withdrawAll();

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.pause();

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.unpause();

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.setAgentSessionKey(attacker);

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.setPayeeWhitelist(attacker, true);

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.setEscrowApproved(attacker, true);

        // Non-agentSessionKey calling spendDirect or fundJob must revert NotAuthorized
        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.spendDirect(whitelistedMerchant, 5_000);

        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.fundJob(address(escrow), providerA, evaluator, 50_000, block.timestamp + 3600);

        // Unapproved escrow calling onEscrowRefunded must revert NotAuthorized
        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.onEscrowRefunded(1, 10_000);

        // Owner can pause, blocking agent spendDirect and fundJob with ContractPaused
        vault.pause();
        _assertEqBool(vault.paused(), true, "vault should be paused");

        vm.prank(agentSessionKey);
        vm.expectRevert(IAgentVault.ContractPaused.selector);
        vault.spendDirect(whitelistedMerchant, 5_000);

        vm.prank(agentSessionKey);
        vm.expectRevert(IAgentVault.ContractPaused.selector);
        vault.fundJob(address(escrow), providerA, evaluator, 50_000, block.timestamp + 3600);

        vault.unpause();
        _assertEqBool(vault.paused(), false, "vault should be unpaused");

        // Owner can configure limits, update session key, withdraw partial and withdrawAll
        address newSession = address(0xA22CE);
        vault.setAgentSessionKey(newSession);
        _assertEqAddr(vault.agentSessionKey(), newSession, "session key updated");
        vault.setAgentSessionKey(agentSessionKey);

        vault.configureLimits(15_000, 70_000, 150_000);
        _assertEqUint(vault.maxPerTxDirect(), 15_000, "direct cap updated");
        _assertEqUint(vault.maxPerTxEscrow(), 70_000, "escrow cap updated");
        _assertEqUint(vault.maxDailySpend(), 150_000, "daily cap updated");
        vault.configureLimits(DEFAULT_DIRECT_CAP, DEFAULT_ESCROW_CAP, DEFAULT_DAILY_CAP);

        uint256 ownerBefore = usdc.balanceOf(owner);
        vault.withdraw(100_000);
        _assertEqUint(usdc.balanceOf(owner) - ownerBefore, 100_000, "owner withdrew 0.1 USDC");
        _assertEqUint(usdc.balanceOf(address(vault)), 400_000, "vault has 0.4 USDC left");

        vault.withdrawAll();
        _assertEqUint(usdc.balanceOf(address(vault)), 0, "vault emptied by withdrawAll");
        _assertEqUint(usdc.balanceOf(owner) - ownerBefore, 500_000, "owner received all 0.5 USDC");
    }

    /// @notice Case-V02: Agent calling spendDirect above maxPerTxDirect (or fundJob above maxPerTxEscrow) must revert.
    function test_Case_V02_ExceedsPerTxDirectAndEscrowCapReverts() public {
        // Exact boundary (0.01 USDC = 10_000) succeeds
        vm.prank(agentSessionKey);
        vault.spendDirect(whitelistedMerchant, 10_000);
        _assertEqUint(usdc.balanceOf(whitelistedMerchant), 10_000, "merchant received 0.01 USDC");

        // 1 unit above maxPerTxDirect (10_001 > 10_000) reverts with ExceedsPerTxDirectCap
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentVault.ExceedsPerTxDirectCap.selector, 10_001, 10_000)
        );
        vault.spendDirect(whitelistedMerchant, 10_001);

        // 1 unit above maxPerTxEscrow (60_001 > 60_000) reverts with ExceedsPerTxEscrowCap
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentVault.ExceedsPerTxEscrowCap.selector, 60_001, 60_000)
        );
        vault.fundJob(address(escrow), providerA, evaluator, 60_001, block.timestamp + 3600);
    }

    /// @notice Case-V03: Agent calling spendDirect to non-whitelisted payee (or unapproved escrow) must revert.
    function test_Case_V03_UnwhitelistedPayeeAndUnapprovedEscrowReverts() public {
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentVault.PayeeNotWhitelisted.selector, unwhitelistedMerchant)
        );
        vault.spendDirect(unwhitelistedMerchant, 3_000);

        address fakeEscrow = address(0xEEEE);
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentVault.EscrowNotApproved.selector, fakeEscrow)
        );
        vault.fundJob(fakeEscrow, providerA, evaluator, 50_000, block.timestamp + 3600);
    }

    /// @notice Case-V04: Cumulative spend reaching maxDailySpend within 24h blocks further tx; resets after 24h; refunds restore quota.
    function test_Case_V04_Rolling24hDailySpendCapAndRefundRestoration() public {
        // Spend 0.06 USDC via escrow + 0.04 USDC via 4 direct spends = 0.10 USDC total
        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(
            address(escrow),
            providerA,
            evaluator,
            60_000,
            block.timestamp + 3600
        );
        _assertEqUint(vault.dailySpendCounter(), 60_000, "daily spend 60_000");

        for (uint256 i = 0; i < 4; i++) {
            vm.prank(agentSessionKey);
            vault.spendDirect(whitelistedMerchant, 10_000);
        }
        _assertEqUint(vault.dailySpendCounter(), 100_000, "daily spend reached 100_000");

        // Next spend of even 1 unit within same 24h window reverts ExceedsDailySpendCap
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentVault.ExceedsDailySpendCap.selector, 100_001, 100_000)
        );
        vault.spendDirect(whitelistedMerchant, 1);

        // When Provider A submits bad data and Evaluator rejects jobId:
        // 5% evaluatorFee (3_000) goes to evaluator, 95% (57_000) is refunded to vault and restores 57_000 of daily quota
        vm.prank(providerA);
        escrow.submitResult(jobId, keccak256("bad_data"), "http://127.0.0.1:18901/deliverables/1");

        vm.prank(evaluator);
        escrow.rejectJob(jobId, "Incomplete report");
        _assertEqUint(vault.dailySpendCounter(), 43_000, "daily spend restored by 57_000 to 43_000 after refund");
        _assertEqUint(usdc.balanceOf(evaluator), 3_000, "evaluator received 3_000 fee on rejectJob");

        // Now Agent can hire Provider B for 57_000 within the same day (43_000 + 57_000 <= 100_000)
        vm.prank(agentSessionKey);
        vault.fundJob(address(escrow), providerB, evaluator, 57_000, block.timestamp + 3600);
        _assertEqUint(vault.dailySpendCounter(), 100_000, "daily spend back to 100_000");

        // Advance time by 1 day (86400s): rolling window resets on next spend (refresh session key TTL too)
        vm.warp(block.timestamp + 1 days);
        vm.prank(agentSessionKey);
        vault.spendDirect(whitelistedMerchant, 10_000);
        _assertEqUint(vault.dailySpendCounter(), 10_000, "window reset to 10_000 after 24h");
    }

    /// @notice Case-V05: SessionKey TTL expiration (`SessionKeyExpired`), `SafeERC20` non-standard token compatibility, and `ReentrancyGuard`.
    function test_Case_V05_SessionKeyExpiryAndSafeERC20AndReentrancyGuard() public {
        // 1. Default sessionKeyExpiry is initialized to block.timestamp + 30 days
        _assertEqUint(vault.sessionKeyExpiry(), block.timestamp + 30 days, "default TTL is 30 days");

        // Owner sets explicit custom expiry via setAgentSessionKeyWithExpiry
        uint256 customExpiry = block.timestamp + 7200;
        vm.prank(attacker);
        vm.expectRevert(IAgentVault.NotAuthorized.selector);
        vault.setAgentSessionKeyWithExpiry(agentSessionKey, customExpiry);

        vault.setAgentSessionKeyWithExpiry(agentSessionKey, customExpiry);
        _assertEqUint(vault.sessionKeyExpiry(), customExpiry, "custom expiry updated");

        // Warp past customExpiry: both spendDirect and fundJob must revert SessionKeyExpired
        vm.warp(customExpiry + 1);
        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentVault.SessionKeyExpired.selector,
                customExpiry,
                customExpiry + 1
            )
        );
        vault.spendDirect(whitelistedMerchant, 5_000);

        vm.prank(agentSessionKey);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentVault.SessionKeyExpired.selector,
                customExpiry,
                customExpiry + 1
            )
        );
        vault.fundJob(address(escrow), providerA, evaluator, 10_000, block.timestamp + 3600);

        // Renewing session key restores ability to spend
        vault.setAgentSessionKey(agentSessionKey);
        _assertEqUint(vault.sessionKeyExpiry(), block.timestamp + 30 days, "renewed TTL +30 days");
        vm.prank(agentSessionKey);
        vault.spendDirect(whitelistedMerchant, 5_000);

        // 2. SafeERC20 compatibility with non-standard ERC20 (no return value on transfer/approve/transferFrom)
        MockNonStandardERC20 usdtLike = new MockNonStandardERC20();
        AgentVault usdtVault = new AgentVault(address(usdtLike), agentSessionKey);
        AgentEscrow usdtEscrow = new AgentEscrow(address(usdtLike));
        usdtVault.setPayeeWhitelist(whitelistedMerchant, true);
        usdtVault.setEscrowApproved(address(usdtEscrow), true);
        usdtLike.mint(address(usdtVault), 200_000);

        vm.prank(agentSessionKey);
        usdtVault.spendDirect(whitelistedMerchant, 10_000);
        _assertEqUint(usdtLike.balanceOf(whitelistedMerchant), 10_000, "USDT-style direct spend succeeded");

        vm.prank(agentSessionKey);
        uint256 usdtJobId = usdtVault.fundJob(address(usdtEscrow), providerB, evaluator, 50_000, block.timestamp + 3600);
        vm.prank(providerB);
        usdtEscrow.submitResult(usdtJobId, keccak256("usdt_result"), "http://127.0.0.1:18901/deliverables/1");
        vm.prank(evaluator);
        usdtEscrow.completeJob(usdtJobId);
        _assertEqUint(usdtLike.balanceOf(providerB), 47_500, "USDT-style provider payout succeeded");
        _assertEqUint(usdtLike.balanceOf(evaluator), 2_500, "USDT-style evaluator fee succeeded");

        // 3. ReentrancyGuard blocks malicious reentrant token callback during spendDirect
        MockReentrantERC20 malToken = new MockReentrantERC20();
        AgentVault malVault = new AgentVault(address(malToken), address(malToken));
        malVault.setPayeeWhitelist(whitelistedMerchant, true);
        malToken.mint(address(malVault), 100_000);
        malToken.setAttack(malVault, whitelistedMerchant, true);

        vm.prank(address(malToken));
        vm.expectRevert(ReentrancyGuard.ReentrancyGuardReentrantCall.selector);
        malVault.spendDirect(whitelistedMerchant, 5_000);

        // Cross-function reentrancy into onEscrowRefunded during spendDirect must also revert
        malVault.setEscrowApproved(address(malToken), true);
        malToken.setAttackRefund(malVault, true);
        vm.prank(address(malToken));
        vm.expectRevert(ReentrancyGuard.ReentrancyGuardReentrantCall.selector);
        malVault.spendDirect(whitelistedMerchant, 5_000);
    }

    // =========================================================================
    // Escrow Unit Tests (Case-E01 ~ Case-E06)
    // =========================================================================

    /// @notice Case-E01: Client locks USDC to create Job; escrow USDC balance increases by exact amount and state is Funded.
    function test_Case_E01_CreateAndFundJobLocksUSDC() public {
        uint256 escrowBefore = usdc.balanceOf(address(escrow));
        uint256 vaultBefore = usdc.balanceOf(address(vault));
        uint256 deadline = block.timestamp + 3600;

        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerA, evaluator, 50_000, deadline);

        _assertEqUint(jobId, 1, "first jobId is 1");
        _assertEqUint(usdc.balanceOf(address(escrow)) - escrowBefore, 50_000, "escrow balance +50_000");
        _assertEqUint(vaultBefore - usdc.balanceOf(address(vault)), 50_000, "vault balance -50_000");

        IAgentEscrow.Job memory job = escrow.jobs(jobId);

        _assertEqUint(job.jobId, 1, "job.jobId == 1");
        _assertEqAddr(job.client, address(vault), "job.client == vault");
        _assertEqAddr(job.provider, providerA, "job.provider == providerA");
        _assertEqAddr(job.evaluator, evaluator, "job.evaluator == evaluator");
        _assertEqUint(job.amount, 50_000, "job.amount == 50_000");
        _assertEqUint(job.evaluatorFee, 2_500, "job.evaluatorFee == 2_500 (5%)");
        _assertEqUint(job.deadline, deadline, "job.deadline == deadline");
        _assertEqUint(job.evaluationDeadline, 0, "job.evaluationDeadline == 0 before submitResult");
        _assertEqBytes32(job.resultHash, bytes32(0), "job.resultHash == 0");
        _assertEqStr(job.dataUri, "", "job.dataUri == empty before submitResult");
        _assertEqUint(uint256(job.state), uint256(IAgentEscrow.JobState.Funded), "job.state == Funded");
    }

    /// @notice Case-E02: Non-Evaluator calling completeJob or rejectJob (and non-Provider calling submitResult) must revert.
    function test_Case_E02_UnauthorizedCallerReverts() public {
        uint256 deadline = block.timestamp + 3600;
        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerA, evaluator, 50_000, deadline);

        // Non-provider trying to submitResult reverts UnauthorizedCaller
        vm.prank(attacker);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.UnauthorizedCaller.selector, attacker, providerA)
        );
        escrow.submitResult(jobId, keccak256("fake"), "http://127.0.0.1:18901/deliverables/1");

        vm.prank(providerA);
        escrow.submitResult(jobId, keccak256("real_deliverable"), "http://127.0.0.1:18901/deliverables/1");

        // Non-evaluator trying to completeJob reverts UnauthorizedCaller
        vm.prank(attacker);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.UnauthorizedCaller.selector, attacker, evaluator)
        );
        escrow.completeJob(jobId);

        // Non-evaluator trying to rejectJob reverts UnauthorizedCaller
        vm.prank(providerA);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.UnauthorizedCaller.selector, providerA, evaluator)
        );
        escrow.rejectJob(jobId, "self reject attempt");
    }

    /// @notice Case-E03: Evaluator passes inspection and calls completeJob; provider receives 95%, evaluator receives 5% fee, and state becomes Completed.
    function test_Case_E03_CompleteJobReleasesFundsToProvider() public {
        uint256 deadline = block.timestamp + 3600;
        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerB, evaluator, 60_000, deadline);

        bytes32 expectedHash = keccak256("30-address-verified-report");
        string memory expectedUri = "http://127.0.0.1:18901/deliverables/1";
        vm.prank(providerB);
        escrow.submitResult(jobId, expectedHash, expectedUri);

        uint256 providerBefore = usdc.balanceOf(providerB);
        uint256 evaluatorBefore = usdc.balanceOf(evaluator);
        vm.prank(evaluator);
        escrow.completeJob(jobId);

        _assertEqUint(usdc.balanceOf(providerB) - providerBefore, 57_000, "providerB received 57_000 USDC (95%)");
        _assertEqUint(usdc.balanceOf(evaluator) - evaluatorBefore, 3_000, "evaluator received 3_000 USDC (5% fee)");
        _assertEqUint(usdc.balanceOf(address(escrow)), 0, "escrow balance is 0");

        IAgentEscrow.Job memory job = escrow.getJob(jobId);
        _assertEqBytes32(job.resultHash, expectedHash, "resultHash preserved");
        _assertEqStr(job.dataUri, expectedUri, "dataUri preserved");
        _assertEqUint(uint256(job.state), uint256(IAgentEscrow.JobState.Completed), "state is Completed");

        // Replay guard: calling completeJob or rejectJob again on Completed job must revert InvalidState
        vm.prank(evaluator);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Completed,
                IAgentEscrow.JobState.Submitted
            )
        );
        escrow.completeJob(jobId);
    }

    /// @notice Case-E04: Evaluator rejects job via rejectJob; evaluator receives 5% fee, client vault receives 95% refund, and state becomes Rejected.
    function test_Case_E04_RejectJobRefundsClientVault() public {
        uint256 deadline = block.timestamp + 3600;
        uint256 vaultBefore = usdc.balanceOf(address(vault));
        uint256 evaluatorBefore = usdc.balanceOf(evaluator);

        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerA, evaluator, 50_000, deadline);
        _assertEqUint(usdc.balanceOf(address(vault)), vaultBefore - 50_000, "50_000 locked");

        vm.prank(providerA);
        escrow.submitResult(jobId, keccak256("empty_garbage_report"), "http://127.0.0.1:18901/deliverables/1");

        vm.prank(evaluator);
        escrow.rejectJob(jobId, "Missing 30 address flows");

        _assertEqUint(usdc.balanceOf(evaluator) - evaluatorBefore, 2_500, "evaluator received 2_500 fee (5%)");
        _assertEqUint(usdc.balanceOf(address(vault)), vaultBefore - 2_500, "vault refunded 47_500 (95%)");
        _assertEqUint(usdc.balanceOf(address(escrow)), 0, "escrow emptied");
        _assertEqUint(vault.dailySpendCounter(), 2_500, "vault daily spend quota restored by 47_500");

        IAgentEscrow.Job memory job = escrow.jobs(jobId);
        _assertEqUint(uint256(job.state), uint256(IAgentEscrow.JobState.Rejected), "state is Rejected");

        // Replay guard: second rejectJob reverts InvalidState
        vm.prank(evaluator);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Rejected,
                IAgentEscrow.JobState.Submitted
            )
        );
        escrow.rejectJob(jobId, "double refund");
    }

    /// @notice Case-E05: Calling claimTimeoutRefund before deadline reverts; calling at/after deadline refunds vault 100% and marks Expired.
    function test_Case_E05_ClaimTimeoutRefundAndDeadlineBoundaries() public {
        uint256 deadline = block.timestamp + 3600;
        uint256 vaultBefore = usdc.balanceOf(address(vault));

        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerA, evaluator, 50_000, deadline);

        // Before deadline: claimTimeoutRefund reverts DeadlineNotReached
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.DeadlineNotReached.selector,
                deadline,
                block.timestamp
            )
        );
        escrow.claimTimeoutRefund(jobId);

        // Advance time past deadline: providerA trying to submitResult after deadline reverts DeadlinePassed
        vm.warp(deadline + 1);
        vm.prank(providerA);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.DeadlinePassed.selector,
                deadline,
                deadline + 1
            )
        );
        escrow.submitResult(jobId, keccak256("too_late"), "http://127.0.0.1:18901/deliverables/1");

        // Now claimTimeoutRefund succeeds and refunds vault 100% (evaluator did not work)
        escrow.claimTimeoutRefund(jobId);
        _assertEqUint(usdc.balanceOf(address(vault)), vaultBefore, "vault refunded after timeout");
        _assertEqUint(vault.dailySpendCounter(), 0, "daily spend quota restored after timeout");

        IAgentEscrow.Job memory job = escrow.jobs(jobId);
        _assertEqUint(uint256(job.state), uint256(IAgentEscrow.JobState.Expired), "state is Expired");

        // Replay guard on claimTimeoutRefund & submitResult when not Funded
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Expired,
                IAgentEscrow.JobState.Funded
            )
        );
        escrow.claimTimeoutRefund(jobId);

        vm.prank(providerA);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Expired,
                IAgentEscrow.JobState.Funded
            )
        );
        escrow.submitResult(jobId, keccak256("expired_job"), "http://127.0.0.1:18901/deliverables/1");
    }

    /// @notice Case-E06: Submitted-state secondary arbitration timeout (`claimEvaluationTimeout`), `evaluatorFeeBps` validation, and `EmptyDataUri` check.
    function test_Case_E06_EvaluationTimeoutAndEvaluatorFeeAndDataUri() public {
        // 1. Owner management of evaluationPeriod and evaluatorFeeBps
        vm.prank(attacker);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.UnauthorizedCaller.selector, attacker, owner)
        );
        escrow.setEvaluationPeriod(7200);

        vm.expectRevert(IAgentEscrow.InvalidEvaluationPeriod.selector);
        escrow.setEvaluationPeriod(0);

        escrow.setEvaluationPeriod(1800);
        _assertEqUint(escrow.evaluationPeriod(), 1800, "evaluationPeriod updated to 1800s");

        vm.prank(attacker);
        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.UnauthorizedCaller.selector, attacker, owner)
        );
        escrow.setEvaluatorFeeBps(300);

        vm.expectRevert(
            abi.encodeWithSelector(IAgentEscrow.FeeTooHigh.selector, 2001, 2000)
        );
        escrow.setEvaluatorFeeBps(2001);

        escrow.setEvaluatorFeeBps(500);
        _assertEqUint(escrow.evaluatorFeeBps(), 500, "evaluatorFeeBps is 500 (5%)");

        // 2. Fund job and test EmptyDataUri revert
        uint256 vaultBefore = usdc.balanceOf(address(vault));
        uint256 deadline = block.timestamp + 3600;
        vm.prank(agentSessionKey);
        uint256 jobId = vault.fundJob(address(escrow), providerA, evaluator, 50_000, deadline);

        // Calling claimEvaluationTimeout while still Funded reverts InvalidState
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Funded,
                IAgentEscrow.JobState.Submitted
            )
        );
        escrow.claimEvaluationTimeout(jobId);

        // Empty dataUri on 3-arg submitResult reverts EmptyDataUri
        vm.prank(providerA);
        vm.expectRevert(IAgentEscrow.EmptyDataUri.selector);
        escrow.submitResult(jobId, keccak256("deliverable"), "");

        // Valid submitResult sets evaluationDeadline = block.timestamp + evaluationPeriod (1800s)
        uint256 submitTs = 1_700_000_000;
        vm.prank(providerA);
        escrow.submitResult(jobId, keccak256("deliverable"), "http://127.0.0.1:18901/deliverables/1");

        IAgentEscrow.Job memory jobSub = escrow.jobs(jobId);
        _assertEqUint(jobSub.evaluationDeadline, submitTs + 1800, "evaluationDeadline set to submitTs + 1800");
        _assertEqStr(jobSub.dataUri, "http://127.0.0.1:18901/deliverables/1", "dataUri stored");
        _assertEqUint(uint256(jobSub.state), uint256(IAgentEscrow.JobState.Submitted), "state is Submitted");

        // Before evaluationDeadline: claimEvaluationTimeout reverts EvaluationDeadlineNotReached
        vm.warp(submitTs + 1799);
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.EvaluationDeadlineNotReached.selector,
                submitTs + 1800,
                submitTs + 1799
            )
        );
        escrow.claimEvaluationTimeout(jobId);

        // At/after evaluationDeadline: claimEvaluationTimeout refunds 100% of job.amount (50_000) to buyer vault and restores daily spend quota
        vm.warp(submitTs + 1800);
        uint256 evalBefore = usdc.balanceOf(evaluator);
        escrow.claimEvaluationTimeout(jobId);

        _assertEqUint(usdc.balanceOf(address(vault)), vaultBefore, "buyer vault refunded 100% on evaluator timeout");
        _assertEqUint(usdc.balanceOf(evaluator), evalBefore, "offline evaluator receives 0 fee");
        _assertEqUint(vault.dailySpendCounter(), 0, "buyer daily spend quota 100% restored");

        IAgentEscrow.Job memory jobExp = escrow.jobs(jobId);
        _assertEqUint(uint256(jobExp.state), uint256(IAgentEscrow.JobState.Expired), "state is Expired");

        // Replay guard: calling claimEvaluationTimeout or completeJob after timeout reverts InvalidState
        vm.expectRevert(
            abi.encodeWithSelector(
                IAgentEscrow.InvalidState.selector,
                IAgentEscrow.JobState.Expired,
                IAgentEscrow.JobState.Submitted
            )
        );
        escrow.claimEvaluationTimeout(jobId);
    }

    /// @notice Additional edge cases for ERC20 transfer failures, direct EOA client in Escrow, and cross-window refund.
    function test_Case_Edge_TransferFailureAndCrossWindowRefund() public {
        // 1. Direct EOA client creating a job directly on AgentEscrow (non-contract client)
        address eoaClient = address(0xC11E);
        usdc.mint(eoaClient, 50_000);
        vm.prank(eoaClient);
        usdc.approve(address(escrow), 50_000);

        vm.prank(eoaClient);
        uint256 eoaJobId = escrow.createAndFundJob(providerA, evaluator, 50_000, block.timestamp + 3600);
        vm.prank(providerA);
        escrow.submitResult(eoaJobId, keccak256("bad"));
        vm.prank(evaluator);
        escrow.rejectJob(eoaJobId, "Rejected for EOA client");
        _assertEqUint(usdc.balanceOf(eoaClient), 47_500, "EOA client refunded 95% (47_500) cleanly");

        // 2. Cross-window refund: job funded in Window 1, refunded in Window 2 does not underflow Window 2 spend
        vm.prank(agentSessionKey);
        uint256 jobW1 = vault.fundJob(address(escrow), providerA, evaluator, 50_000, block.timestamp + 2 days);
        vm.warp(block.timestamp + 1 days + 10);
        // Spend 10_000 in Window 2
        vm.prank(agentSessionKey);
        vault.spendDirect(whitelistedMerchant, 10_000);
        _assertEqUint(vault.dailySpendCounter(), 10_000, "Window 2 counter is 10_000");

        // Refund jobW1 (from Window 1) during Window 2
        vm.prank(providerA);
        escrow.submitResult(jobW1, keccak256("late_bad"));
        vm.prank(evaluator);
        escrow.rejectJob(jobW1, "Window 1 job rejected in Window 2");
        _assertEqUint(vault.dailySpendCounter(), 10_000, "Window 2 counter unaffected by Window 1 refund");

        // 3. ERC20 TransferFailed branches
        usdc.setFailTransfers(true);

        vm.prank(agentSessionKey);
        vm.expectRevert(IAgentVault.TransferFailed.selector);
        vault.spendDirect(whitelistedMerchant, 5_000);

        vm.prank(agentSessionKey);
        vm.expectRevert(IAgentVault.TransferFailed.selector);
        vault.fundJob(address(escrow), providerA, evaluator, 10_000, block.timestamp + 3600);

        vm.expectRevert(IAgentVault.TransferFailed.selector);
        vault.withdraw(1_000);

        vm.expectRevert(IAgentVault.TransferFailed.selector);
        vault.withdrawAll();

        vm.prank(eoaClient);
        vm.expectRevert(IAgentEscrow.TransferFailed.selector);
        escrow.createAndFundJob(providerA, evaluator, 10_000, block.timestamp + 3600);

        usdc.setFailTransfers(false);

        // Also test TransferFailed on completeJob and _refundClient (rejectJob)
        vm.prank(agentSessionKey);
        uint256 jobFail1 = vault.fundJob(address(escrow), providerA, evaluator, 10_000, block.timestamp + 3600);
        vm.prank(providerA);
        escrow.submitResult(jobFail1, keccak256("res"));

        usdc.setFailTransfers(true);
        vm.prank(evaluator);
        vm.expectRevert(IAgentEscrow.TransferFailed.selector);
        escrow.completeJob(jobFail1);

        vm.prank(evaluator);
        vm.expectRevert(IAgentEscrow.TransferFailed.selector);
        escrow.rejectJob(jobFail1, "transfer fail on refund");
        usdc.setFailTransfers(false);
    }
}
