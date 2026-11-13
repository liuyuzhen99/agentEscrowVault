// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IAgentEscrow {
    enum JobState {
        None,        // 0: Does not exist
        Funded,      // 1: Funds locked, awaiting provider delivery
        Submitted,   // 2: Provider submitted resultHash + dataUri, awaiting evaluator inspection
        Completed,   // 3: Inspection passed, funds released to provider + evaluator fee (terminal)
        Rejected,    // 4: Inspection failed, funds refunded 100% to client (terminal)
        Expired      // 5: Timed out in Funded or Submitted, refunded 100% to client (terminal)
    }

    struct Job {
        uint256 jobId;
        address client;
        address provider;
        address evaluator;
        uint256 amount;
        uint256 evaluatorFee;
        uint256 deadline;
        uint256 evaluationDeadline;
        bytes32 resultHash;
        string dataUri;
        JobState state;
    }

    event JobCreated(
        uint256 indexed jobId,
        address indexed client,
        address indexed provider,
        uint256 amount,
        uint256 deadline
    );
    event ResultSubmitted(uint256 indexed jobId, bytes32 resultHash, string dataUri, uint256 evaluationDeadline);
    event JobCompleted(uint256 indexed jobId, address indexed provider, uint256 amount);
    event JobRejected(uint256 indexed jobId, address indexed client, uint256 amount, string reason);
    event JobExpired(uint256 indexed jobId, address indexed client, uint256 amount);
    event EvaluatorFeePaid(uint256 indexed jobId, address indexed evaluator, uint256 fee);
    event EvaluationTimeoutClaimed(uint256 indexed jobId, address indexed client, uint256 amount);
    event EvaluatorStaked(address indexed evaluator, uint256 amount, uint256 totalStake);
    event EvaluatorUnstaked(address indexed evaluator, uint256 amount, uint256 remainingStake);
    event EvaluatorSlashed(
        uint256 indexed jobId,
        address indexed evaluator,
        address indexed recipient,
        uint256 slashAmount,
        string reason
    );
    event EncryptionPublicKeyRegistered(address indexed account, bytes pubKey);
    event ProviderStaked(address indexed provider, uint256 amount, uint256 totalStake);
    event ProviderUnstaked(address indexed provider, uint256 amount, uint256 remainingStake);
    event ProviderBondLocked(uint256 indexed jobId, address indexed provider, uint256 bondAmount);
    event ProviderBondUnlocked(uint256 indexed jobId, address indexed provider, uint256 bondAmount);
    event ProviderBondSlashedToEvaluator(
        uint256 indexed jobId,
        address indexed provider,
        address indexed evaluator,
        uint256 bondAmount
    );
    event DisputeRaised(uint256 indexed jobId, address indexed disputant, string reason);

    error InvalidState(JobState current, JobState expected);
    error UnauthorizedCaller(address caller, address expected);
    error ConflictingParties();
    error DeadlinePassed(uint256 deadline, uint256 current);
    error DeadlineNotReached(uint256 deadline, uint256 current);
    error EvaluationDeadlineNotReached(uint256 evaluationDeadline, uint256 current);
    error EmptyDataUri();
    error FeeTooHigh(uint256 requestedBps, uint256 maxBps);
    error InvalidEvaluationPeriod();
    error InsufficientEvaluatorStake(uint256 currentStake, uint256 requiredStake);
    error InsufficientProviderBond(uint256 availableStake, uint256 requiredBond);
    error InvalidSlashAmount(uint256 requested, uint256 available);
    error InvalidRecipient();
    error InvalidPublicKey();
    error DisputeNotRaised(uint256 jobId);
    error TransferFailed();

    function createAndFundJob(
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external returns (uint256 jobId);

    function submitResult(uint256 jobId, bytes32 resultHash, string calldata dataUri) external;
    function submitResult(uint256 jobId, bytes32 resultHash) external;
    function completeJob(uint256 jobId) external;
    function rejectJob(uint256 jobId, string calldata reason) external;
    function claimTimeoutRefund(uint256 jobId) external;
    function claimEvaluationTimeout(uint256 jobId) external;

    function registerEncryptionPublicKey(bytes calldata pubKey) external;
    function registerVaultEncryptionPublicKey(address vault, bytes calldata pubKey) external;
    function getEncryptionPublicKey(address account) external view returns (bytes memory);

    function setEvaluationPeriod(uint256 newPeriod) external;
    function setEvaluatorFeeBps(uint256 newFeeBps) external;
    function setMinEvaluatorStake(uint256 newMinStake) external;
    function setRequireProviderBond(bool required) external;
    function stakeEvaluator(uint256 amount) external;
    function unstakeEvaluator(uint256 amount) external;
    function stakeProvider(uint256 amount) external;
    function unstakeProvider(uint256 amount) external;
    function raiseDispute(uint256 jobId, string calldata reason) external;
    function slashEvaluator(
        uint256 jobId,
        address recipient,
        uint256 slashAmount,
        string calldata reason
    ) external;
    function minEvaluatorStake() external view returns (uint256);
    function requireProviderBond() external view returns (bool);
    function evaluatorStakes(address evaluator) external view returns (uint256);
    function providerStakes(address provider) external view returns (uint256);
    function jobProviderBonds(uint256 jobId) external view returns (uint256);
    function jobDisputed(uint256 jobId) external view returns (bool);
    function jobDisputant(uint256 jobId) external view returns (address);
    function jobs(uint256 jobId) external view returns (Job memory);
    function getJob(uint256 jobId) external view returns (Job memory);
}
