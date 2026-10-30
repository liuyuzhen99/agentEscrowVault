// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "./IERC20.sol";
import {IAgentVault} from "./IAgentVault.sol";
import {IAgentEscrow} from "./IAgentEscrow.sol";

contract AgentEscrow is IAgentEscrow {
    IERC20 public immutable usdc;
    uint256 public nextJobId;

    mapping(uint256 => Job) public jobs;

    constructor(address usdcAddress) {
        usdc = IERC20(usdcAddress);
    }

    function createAndFundJob(
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external override returns (uint256 jobId) {
        if (!usdc.transferFrom(msg.sender, address(this), amount)) {
            revert TransferFailed();
        }

        jobId = ++nextJobId;
        jobs[jobId] = Job({
            jobId: jobId,
            client: msg.sender,
            provider: provider,
            evaluator: evaluator,
            amount: amount,
            deadline: deadline,
            resultHash: bytes32(0),
            state: JobState.Funded
        });

        emit JobCreated(jobId, msg.sender, provider, amount, deadline);
    }

    function submitResult(uint256 jobId, bytes32 resultHash) external override {
        Job storage job = jobs[jobId];
        if (job.state != JobState.Funded) {
            revert InvalidState(job.state, JobState.Funded);
        }
        if (msg.sender != job.provider) {
            revert UnauthorizedCaller(msg.sender, job.provider);
        }
        if (block.timestamp > job.deadline) {
            revert DeadlinePassed(job.deadline, block.timestamp);
        }

        job.resultHash = resultHash;
        job.state = JobState.Submitted;

        emit ResultSubmitted(jobId, resultHash);
    }

    function completeJob(uint256 jobId) external override {
        Job storage job = jobs[jobId];
        if (job.state != JobState.Submitted) {
            revert InvalidState(job.state, JobState.Submitted);
        }
        if (msg.sender != job.evaluator) {
            revert UnauthorizedCaller(msg.sender, job.evaluator);
        }

        job.state = JobState.Completed;
        if (!usdc.transfer(job.provider, job.amount)) {
            revert TransferFailed();
        }

        emit JobCompleted(jobId, job.provider, job.amount);
    }

    function rejectJob(uint256 jobId, string calldata reason) external override {
        Job storage job = jobs[jobId];
        if (job.state != JobState.Submitted) {
            revert InvalidState(job.state, JobState.Submitted);
        }
        if (msg.sender != job.evaluator) {
            revert UnauthorizedCaller(msg.sender, job.evaluator);
        }

        job.state = JobState.Rejected;
        _refundClient(job.client, jobId, job.amount);

        emit JobRejected(jobId, job.client, job.amount, reason);
    }

    function claimTimeoutRefund(uint256 jobId) external override {
        Job storage job = jobs[jobId];
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

    function _refundClient(address client, uint256 jobId, uint256 amount) internal {
        if (!usdc.transfer(client, amount)) {
            revert TransferFailed();
        }
        if (client.code.length > 0) {
            IAgentVault(client).onEscrowRefunded(jobId, amount);
        }
    }
}
