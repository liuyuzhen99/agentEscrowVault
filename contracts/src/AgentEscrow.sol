// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "./IERC20.sol";
import {SafeERC20} from "./SafeERC20.sol";
import {ReentrancyGuard} from "./ReentrancyGuard.sol";
import {IAgentVault} from "./IAgentVault.sol";
import {IAgentEscrow} from "./IAgentEscrow.sol";

contract AgentEscrow is IAgentEscrow, ReentrancyGuard {
    using SafeERC20 for IERC20;

    uint256 public constant MAX_FEE_BPS = 2_000; // Max 20%
    uint256 public constant BPS_DENOMINATOR = 10_000;

    address public immutable owner;
    IERC20 public immutable usdc;
    uint256 public nextJobId;

    uint256 public evaluationPeriod = 1 hours;
    uint256 public evaluatorFeeBps = 500; // Default 5% (500 bps)
    uint256 public minEvaluatorStake;
    bool public requireProviderBond;

    mapping(address => uint256) public evaluatorStakes;
    mapping(address => uint256) public providerStakes;
    mapping(uint256 => uint256) public jobProviderBonds;
    mapping(uint256 => bool) public jobDisputed;
    mapping(uint256 => address) public jobDisputant;
    mapping(address => bytes) public encryptionPublicKeys;
    mapping(uint256 => Job) private _jobs;

    constructor(address usdcAddress) {
        owner = msg.sender;
        usdc = IERC20(usdcAddress);
    }

    function jobs(uint256 jobId) external view override returns (Job memory) {
        return _jobs[jobId];
    }

    function getJob(uint256 jobId) external view override returns (Job memory) {
        return _jobs[jobId];
    }

    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert UnauthorizedCaller(msg.sender, owner);
        }
        _;
    }

    function _deriveAddressFromPubKey(bytes calldata pubKey) internal pure returns (address) {
        if (pubKey.length != 65 || pubKey[0] != 0x04) {
            revert InvalidPublicKey();
        }
        return address(uint160(uint256(keccak256(pubKey[1:]))));
    }

    function registerEncryptionPublicKey(bytes calldata pubKey) external override {
        address derived = _deriveAddressFromPubKey(pubKey);
        if (derived != msg.sender) {
            revert InvalidPublicKey();
        }
        encryptionPublicKeys[msg.sender] = pubKey;
        emit EncryptionPublicKeyRegistered(msg.sender, pubKey);
    }

    function registerVaultEncryptionPublicKey(address vault, bytes calldata pubKey) external override {
        if (vault == address(0) || vault.code.length == 0) {
            revert InvalidRecipient();
        }
        address vaultOwner = IAgentVault(vault).owner();
        address vaultSessionKey = IAgentVault(vault).agentSessionKey();
        if (msg.sender != vaultOwner && msg.sender != vaultSessionKey) {
            revert UnauthorizedCaller(msg.sender, vaultSessionKey);
        }
        address keySigner = _deriveAddressFromPubKey(pubKey);
        if (keySigner != vaultSessionKey && keySigner != vaultOwner) {
            revert InvalidPublicKey();
        }
        encryptionPublicKeys[vault] = pubKey;
        emit EncryptionPublicKeyRegistered(vault, pubKey);
    }

    function getEncryptionPublicKey(address account) external view override returns (bytes memory) {
        return encryptionPublicKeys[account];
    }

    function setEvaluationPeriod(uint256 newPeriod) external override onlyOwner {
        if (newPeriod == 0) revert InvalidEvaluationPeriod();
        evaluationPeriod = newPeriod;
    }

    function setEvaluatorFeeBps(uint256 newFeeBps) external override onlyOwner {
        if (newFeeBps > MAX_FEE_BPS) {
            revert FeeTooHigh(newFeeBps, MAX_FEE_BPS);
        }
        evaluatorFeeBps = newFeeBps;
    }

    function setMinEvaluatorStake(uint256 newMinStake) external override onlyOwner {
        minEvaluatorStake = newMinStake;
    }

    function setRequireProviderBond(bool required) external override onlyOwner {
        requireProviderBond = required;
    }

    function stakeEvaluator(uint256 amount) external override nonReentrant {
        if (amount == 0) {
            revert InvalidSlashAmount(0, evaluatorStakes[msg.sender]);
        }
        usdc.safeTransferFrom(msg.sender, address(this), amount);
        uint256 newStake = evaluatorStakes[msg.sender] + amount;
        evaluatorStakes[msg.sender] = newStake;
        emit EvaluatorStaked(msg.sender, amount, newStake);
    }

    function unstakeEvaluator(uint256 amount) external override nonReentrant {
        uint256 available = evaluatorStakes[msg.sender];
        if (amount == 0 || amount > available) {
            revert InvalidSlashAmount(amount, available);
        }
        uint256 remaining = available - amount;
        evaluatorStakes[msg.sender] = remaining;
        usdc.safeTransfer(msg.sender, amount);
        emit EvaluatorUnstaked(msg.sender, amount, remaining);
    }

    function stakeProvider(uint256 amount) external override nonReentrant {
        if (amount == 0) {
            revert InvalidSlashAmount(0, providerStakes[msg.sender]);
        }
        usdc.safeTransferFrom(msg.sender, address(this), amount);
        uint256 newStake = providerStakes[msg.sender] + amount;
        providerStakes[msg.sender] = newStake;
        emit ProviderStaked(msg.sender, amount, newStake);
    }

    function unstakeProvider(uint256 amount) external override nonReentrant {
        uint256 available = providerStakes[msg.sender];
        if (amount == 0 || amount > available) {
            revert InvalidSlashAmount(amount, available);
        }
        uint256 remaining = available - amount;
        providerStakes[msg.sender] = remaining;
        usdc.safeTransfer(msg.sender, amount);
        emit ProviderUnstaked(msg.sender, amount, remaining);
    }

    function _isAuthorizedDisputant(Job storage job, address caller) internal view returns (bool) {
        if (caller == job.client || caller == job.provider) {
            return true;
        }
        if (job.client.code.length > 0) {
            return (
                caller == IAgentVault(job.client).agentSessionKey() ||
                caller == IAgentVault(job.client).owner()
            );
        }
        return false;
    }

    function raiseDispute(uint256 jobId, string calldata reason) external override {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Completed && job.state != JobState.Rejected) {
            revert InvalidState(job.state, JobState.Completed);
        }
        if (!_isAuthorizedDisputant(job, msg.sender)) {
            revert UnauthorizedCaller(msg.sender, job.client);
        }
        jobDisputed[jobId] = true;
        jobDisputant[jobId] = msg.sender;
        emit DisputeRaised(jobId, msg.sender, reason);
    }

    function slashEvaluator(
        uint256 jobId,
        address recipient,
        uint256 slashAmount,
        string calldata reason
    ) external override nonReentrant onlyOwner {
        Job storage job = _jobs[jobId];
        address ev = job.evaluator;
        if (
            ev == address(0) ||
            recipient == address(0) ||
            recipient == owner ||
            (recipient != job.client && recipient != job.provider)
        ) {
            revert InvalidRecipient();
        }
        if (!jobDisputed[jobId]) {
            revert DisputeNotRaised(jobId);
        }
        uint256 available = evaluatorStakes[ev];
        if (slashAmount == 0 || slashAmount > available) {
            revert InvalidSlashAmount(slashAmount, available);
        }
        evaluatorStakes[ev] = available - slashAmount;
        usdc.safeTransfer(recipient, slashAmount);
        emit EvaluatorSlashed(jobId, ev, recipient, slashAmount, reason);
    }

    function createAndFundJob(
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external override nonReentrant returns (uint256 jobId) {
        if (
            provider == address(0) ||
            evaluator == address(0) ||
            provider == evaluator ||
            provider == msg.sender ||
            evaluator == msg.sender
        ) {
            revert ConflictingParties();
        }
        usdc.safeTransferFrom(msg.sender, address(this), amount);

        uint256 fee = (amount * evaluatorFeeBps) / BPS_DENOMINATOR;
        jobId = ++nextJobId;
        _jobs[jobId] = Job({
            jobId: jobId,
            client: msg.sender,
            provider: provider,
            evaluator: evaluator,
            amount: amount,
            evaluatorFee: fee,
            deadline: deadline,
            evaluationDeadline: 0,
            resultHash: bytes32(0),
            dataUri: "",
            state: JobState.Funded
        });

        emit JobCreated(jobId, msg.sender, provider, amount, deadline);
    }

    function submitResult(
        uint256 jobId,
        bytes32 resultHash,
        string calldata dataUri
    ) external override nonReentrant {
        if (bytes(dataUri).length == 0) {
            revert EmptyDataUri();
        }
        _submitResult(jobId, resultHash, dataUri);
    }

    function submitResult(uint256 jobId, bytes32 resultHash) external override nonReentrant {
        _submitResult(jobId, resultHash, "legacy://in-memory");
    }

    function _submitResult(uint256 jobId, bytes32 resultHash, string memory dataUri) internal {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Funded) {
            revert InvalidState(job.state, JobState.Funded);
        }
        if (msg.sender != job.provider) {
            revert UnauthorizedCaller(msg.sender, job.provider);
        }
        if (block.timestamp > job.deadline) {
            revert DeadlinePassed(job.deadline, block.timestamp);
        }

        uint256 requiredBond = job.evaluatorFee;
        uint256 availableStake = providerStakes[msg.sender];
        if (availableStake >= requiredBond && requiredBond > 0) {
            providerStakes[msg.sender] = availableStake - requiredBond;
            jobProviderBonds[jobId] = requiredBond;
            emit ProviderBondLocked(jobId, msg.sender, requiredBond);
        } else if (requireProviderBond) {
            revert InsufficientProviderBond(availableStake, requiredBond);
        }

        uint256 evalDeadline = block.timestamp + evaluationPeriod;
        job.resultHash = resultHash;
        job.dataUri = dataUri;
        job.evaluationDeadline = evalDeadline;
        job.state = JobState.Submitted;

        emit ResultSubmitted(jobId, resultHash, dataUri, evalDeadline);
    }

    function completeJob(uint256 jobId) external override nonReentrant {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Submitted) {
            revert InvalidState(job.state, JobState.Submitted);
        }
        if (msg.sender != job.evaluator) {
            revert UnauthorizedCaller(msg.sender, job.evaluator);
        }
        if (evaluatorStakes[msg.sender] < minEvaluatorStake) {
            revert InsufficientEvaluatorStake(evaluatorStakes[msg.sender], minEvaluatorStake);
        }

        job.state = JobState.Completed;
        uint256 fee = job.evaluatorFee;
        uint256 providerPayout = job.amount - fee;

        uint256 lockedBond = jobProviderBonds[jobId];
        if (lockedBond > 0) {
            jobProviderBonds[jobId] = 0;
            providerStakes[job.provider] += lockedBond;
            emit ProviderBondUnlocked(jobId, job.provider, lockedBond);
        }

        if (fee > 0) {
            usdc.safeTransfer(job.evaluator, fee);
            emit EvaluatorFeePaid(jobId, job.evaluator, fee);
        }
        usdc.safeTransfer(job.provider, providerPayout);

        emit JobCompleted(jobId, job.provider, providerPayout);
    }

    function rejectJob(uint256 jobId, string calldata reason) external override nonReentrant {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Submitted) {
            revert InvalidState(job.state, JobState.Submitted);
        }
        if (msg.sender != job.evaluator) {
            revert UnauthorizedCaller(msg.sender, job.evaluator);
        }
        if (evaluatorStakes[msg.sender] < minEvaluatorStake) {
            revert InsufficientEvaluatorStake(evaluatorStakes[msg.sender], minEvaluatorStake);
        }

        job.state = JobState.Rejected;
        uint256 refundAmount = job.amount;

        uint256 lockedBond = jobProviderBonds[jobId];
        if (lockedBond > 0) {
            jobProviderBonds[jobId] = 0;
            usdc.safeTransfer(job.evaluator, lockedBond);
            emit ProviderBondSlashedToEvaluator(jobId, job.provider, job.evaluator, lockedBond);
            emit EvaluatorFeePaid(jobId, job.evaluator, lockedBond);
        }

        _refundClient(job.client, jobId, refundAmount);

        emit JobRejected(jobId, job.client, refundAmount, reason);
    }

    function claimTimeoutRefund(uint256 jobId) external override nonReentrant {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Funded) {
            revert InvalidState(job.state, JobState.Funded);
        }
        if (block.timestamp < job.deadline) {
            revert DeadlineNotReached(job.deadline, block.timestamp);
        }

        job.state = JobState.Expired;
        _refundClient(job.client, jobId, job.amount);

        emit JobExpired(jobId, job.client, job.amount);
    }

    function claimEvaluationTimeout(uint256 jobId) external override nonReentrant {
        Job storage job = _jobs[jobId];
        if (job.state != JobState.Submitted) {
            revert InvalidState(job.state, JobState.Submitted);
        }
        if (block.timestamp < job.evaluationDeadline) {
            revert EvaluationDeadlineNotReached(job.evaluationDeadline, block.timestamp);
        }

        job.state = JobState.Expired;

        uint256 lockedBond = jobProviderBonds[jobId];
        if (lockedBond > 0) {
            jobProviderBonds[jobId] = 0;
            providerStakes[job.provider] += lockedBond;
            emit ProviderBondUnlocked(jobId, job.provider, lockedBond);
        }

        uint256 evalStake = evaluatorStakes[job.evaluator];
        uint256 slashPenalty = job.evaluatorFee < evalStake ? job.evaluatorFee : evalStake;
        if (slashPenalty > 0) {
            evaluatorStakes[job.evaluator] = evalStake - slashPenalty;
            usdc.safeTransfer(job.provider, slashPenalty);
            emit EvaluatorSlashed(jobId, job.evaluator, job.provider, slashPenalty, "EvaluationTimeout");
        }

        _refundClient(job.client, jobId, job.amount);

        emit EvaluationTimeoutClaimed(jobId, job.client, job.amount);
        emit JobExpired(jobId, job.client, job.amount);
    }

    function _refundClient(address client, uint256 jobId, uint256 amount) internal {
        usdc.safeTransfer(client, amount);
        if (client.code.length > 0) {
            IAgentVault(client).onEscrowRefunded(jobId, amount);
        }
    }
}
