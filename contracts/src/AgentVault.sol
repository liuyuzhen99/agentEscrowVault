// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "./IERC20.sol";
import {SafeERC20} from "./SafeERC20.sol";
import {ReentrancyGuard} from "./ReentrancyGuard.sol";
import {IAgentVault} from "./IAgentVault.sol";
import {IAgentEscrow} from "./IAgentEscrow.sol";

contract AgentVault is IAgentVault, ReentrancyGuard {
    using SafeERC20 for IERC20;

    address public immutable owner;
    address public agentSessionKey;
    uint256 public sessionKeyExpiry;
    IERC20 public immutable usdc;

    uint256 public maxPerTxDirect;
    uint256 public maxPerTxEscrow;
    uint256 public maxDailySpend;

    bool public paused;

    mapping(address => bool) public isWhitelistedPayee;
    mapping(address => bool) public isApprovedEscrow;

    uint256 public dailySpendCounter;
    uint256 public windowStartTimestamp;

    // Tracks the windowStartTimestamp under which an escrow jobId was funded so refunds
    // only restore quota when occurring within the same 24-hour window.
    mapping(address => mapping(uint256 => uint256)) private _jobFundedWindow;

    uint256 private constant DEFAULT_DIRECT_CAP = 10_000;   // 0.01 USDC (6 decimals)
    uint256 private constant DEFAULT_ESCROW_CAP = 60_000;   // 0.06 USDC
    uint256 private constant DEFAULT_DAILY_CAP  = 100_000;  // 0.10 USDC
    uint256 private constant DEFAULT_SESSION_TTL = 30 days;

    constructor(address usdcAddress, address initialSessionKey) {
        owner = msg.sender;
        usdc = IERC20(usdcAddress);
        agentSessionKey = initialSessionKey;
        sessionKeyExpiry = block.timestamp + DEFAULT_SESSION_TTL;

        maxPerTxDirect = DEFAULT_DIRECT_CAP;
        maxPerTxEscrow = DEFAULT_ESCROW_CAP;
        maxDailySpend = DEFAULT_DAILY_CAP;

        windowStartTimestamp = block.timestamp;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotAuthorized();
        _;
    }

    modifier onlyAgent() {
        if (msg.sender != agentSessionKey) revert NotAuthorized();
        if (paused) revert ContractPaused();
        if (block.timestamp > sessionKeyExpiry) {
            revert SessionKeyExpired(sessionKeyExpiry, block.timestamp);
        }
        _;
    }

    function _checkAndUpdateDailySpend(uint256 amount) internal {
        if (block.timestamp >= windowStartTimestamp + 1 days) {
            windowStartTimestamp = block.timestamp;
            dailySpendCounter = 0;
        }
        uint256 newTotal = dailySpendCounter + amount;
        if (newTotal > maxDailySpend) {
            revert ExceedsDailySpendCap(newTotal, maxDailySpend);
        }
        dailySpendCounter = newTotal;
    }

    function spendDirect(address to, uint256 amount) external override nonReentrant onlyAgent {
        if (!isWhitelistedPayee[to]) revert PayeeNotWhitelisted(to);
        if (amount > maxPerTxDirect) revert ExceedsPerTxDirectCap(amount, maxPerTxDirect);

        _checkAndUpdateDailySpend(amount);

        usdc.safeTransfer(to, amount);
        emit DirectSpendExecuted(to, amount);
    }

    function fundJob(
        address escrow,
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external override nonReentrant onlyAgent returns (uint256 jobId) {
        if (!isApprovedEscrow[escrow]) revert EscrowNotApproved(escrow);
        if (amount > maxPerTxEscrow) revert ExceedsPerTxEscrowCap(amount, maxPerTxEscrow);

        _checkAndUpdateDailySpend(amount);

        usdc.safeApprove(escrow, amount);
        jobId = IAgentEscrow(escrow).createAndFundJob(provider, evaluator, amount, deadline);
        _jobFundedWindow[escrow][jobId] = windowStartTimestamp;

        emit EscrowFunded(escrow, jobId, amount);
    }

    function onEscrowRefunded(uint256 jobId, uint256 amount) external override nonReentrant {
        if (!isApprovedEscrow[msg.sender]) revert NotAuthorized();
        if (
            _jobFundedWindow[msg.sender][jobId] == windowStartTimestamp &&
            dailySpendCounter >= amount
        ) {
            dailySpendCounter -= amount;
        }
        delete _jobFundedWindow[msg.sender][jobId];
        emit EscrowRefunded(msg.sender, jobId, amount);
    }

    function pause() external override onlyOwner {
        paused = true;
        emit KillSwitchToggled(true);
    }

    function unpause() external override onlyOwner {
        paused = false;
        emit KillSwitchToggled(false);
    }

    function withdraw(uint256 amount) external override nonReentrant onlyOwner {
        usdc.safeTransfer(owner, amount);
        emit FundsWithdrawn(owner, amount);
    }

    function withdrawAll() external override nonReentrant onlyOwner {
        uint256 balance = usdc.balanceOf(address(this));
        usdc.safeTransfer(owner, balance);
        emit FundsWithdrawn(owner, balance);
    }

    function setAgentSessionKey(address newKey) external override onlyOwner {
        uint256 expiry = block.timestamp + DEFAULT_SESSION_TTL;
        agentSessionKey = newKey;
        sessionKeyExpiry = expiry;
        emit SessionKeyUpdated(newKey, expiry);
    }

    function setAgentSessionKeyWithExpiry(address newKey, uint256 expiry) external override onlyOwner {
        agentSessionKey = newKey;
        sessionKeyExpiry = expiry;
        emit SessionKeyUpdated(newKey, expiry);
    }

    function configureLimits(
        uint256 directCap,
        uint256 escrowCap,
        uint256 dailyCap
    ) external override onlyOwner {
        maxPerTxDirect = directCap;
        maxPerTxEscrow = escrowCap;
        maxDailySpend = dailyCap;
    }

    function setPayeeWhitelist(address payee, bool allowed) external override onlyOwner {
        isWhitelistedPayee[payee] = allowed;
    }

    function setEscrowApproved(address escrow, bool approved) external override onlyOwner {
        isApprovedEscrow[escrow] = approved;
    }
}
