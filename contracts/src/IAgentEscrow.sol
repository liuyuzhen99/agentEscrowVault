// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IAgentEscrow {
    enum JobState {
        None,        // 0: Does not exist
        Funded,      // 1: Funds locked, awaiting provider delivery
        Submitted,   // 2: Provider submitted resultHash, awaiting evaluator inspection
        Completed,   // 3: Inspection passed, funds released to provider (terminal)
        Rejected,    // 4: Inspection failed, funds refunded to client (terminal)
        Expired      // 5: Timed out without submission, refunded to client (terminal)
    }

    struct Job {
        uint256 jobId;
        address client;
        address provider;
        address evaluator;
        uint256 amount;
        uint256 deadline;
        bytes32 resultHash;
        JobState state;
    }

    event JobCreated(
        uint256 indexed jobId,
        address indexed client,
        address indexed provider,
        uint256 amount,
        uint256 deadline
    );
    event ResultSubmitted(uint256 indexed jobId, bytes32 resultHash);
    event JobCompleted(uint256 indexed jobId, address indexed provider, uint256 amount);
    event JobRejected(uint256 indexed jobId, address indexed client, uint256 amount, string reason);
    event JobExpired(uint256 indexed jobId, address indexed client, uint256 amount);

    error InvalidState(JobState current, JobState expected);
    error UnauthorizedCaller(address caller, address expected);
    error DeadlinePassed(uint256 deadline, uint256 current);
    error DeadlineNotReached(uint256 deadline, uint256 current);
    error TransferFailed();

    function createAndFundJob(
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external returns (uint256 jobId);

    function submitResult(uint256 jobId, bytes32 resultHash) external;
    function completeJob(uint256 jobId) external;
    function rejectJob(uint256 jobId, string calldata reason) external;
    function claimTimeoutRefund(uint256 jobId) external;
}
