// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// @title ReentrancyGuard
/// @notice Standard non-reentrant mutex lock for state-mutating financial entrypoints.
abstract contract ReentrancyGuard {
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;

    uint256 private _status = NOT_ENTERED;

    error ReentrancyGuardReentrantCall();

    modifier nonReentrant() {
        if (_status == ENTERED) {
            revert ReentrancyGuardReentrantCall();
        }
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;
    }
}
