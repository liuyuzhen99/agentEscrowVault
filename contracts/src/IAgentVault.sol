// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IAgentVault {
    event DirectSpendExecuted(address indexed to, uint256 amount);
    event EscrowFunded(address indexed escrow, uint256 indexed jobId, uint256 amount);
    event EscrowRefunded(address indexed escrow, uint256 indexed jobId, uint256 amount);
    event FundsWithdrawn(address indexed to, uint256 amount);
    event KillSwitchToggled(bool isPaused);
    event SessionKeyUpdated(address indexed newKey, uint256 expiry);

    error NotAuthorized();
    error ContractPaused();
    error SessionKeyExpired(uint256 expiry, uint256 current);
    error ExceedsPerTxDirectCap(uint256 requested, uint256 max);
    error ExceedsPerTxEscrowCap(uint256 requested, uint256 max);
    error ExceedsDailySpendCap(uint256 requested, uint256 max);
    error PayeeNotWhitelisted(address payee);
    error EscrowNotApproved(address escrow);
    error TransferFailed();

    function spendDirect(address to, uint256 amount) external;
    function fundJob(
        address escrow,
        address provider,
        address evaluator,
        uint256 amount,
        uint256 deadline
    ) external returns (uint256 jobId);
    function onEscrowRefunded(uint256 jobId, uint256 amount) external;

    // Human owner management functions
    function pause() external;
    function unpause() external;
    function withdraw(uint256 amount) external;
    function withdrawAll() external;
    function setAgentSessionKey(address newKey) external;
    function setAgentSessionKeyWithExpiry(address newKey, uint256 expiry) external;
    function configureLimits(uint256 directCap, uint256 escrowCap, uint256 dailyCap) external;
    function setPayeeWhitelist(address payee, bool allowed) external;
    function setEscrowApproved(address escrow, bool approved) external;
}
