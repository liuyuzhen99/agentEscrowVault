// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "./IERC20.sol";

/// @title SafeERC20
/// @notice Low-level ERC20 call wrapper supporting both standard tokens (returning bool)
///         and non-standard tokens like USDT (returning empty returndata).
library SafeERC20 {
    error TransferFailed();

    function safeTransfer(IERC20 token, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeCall(token.transfer, (to, value)));
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeCall(token.transferFrom, (from, to, value)));
    }

    function safeApprove(IERC20 token, address spender, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeCall(token.approve, (spender, value)));
    }

    function _callOptionalReturn(IERC20 token, bytes memory data) private {
        (bool success, bytes memory returndata) = address(token).call(data);
        if (!success) {
            if (returndata.length > 0) {
                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            }
            revert TransferFailed();
        }
        if (returndata.length > 0 && !abi.decode(returndata, (bool))) {
            revert TransferFailed();
        }
    }
}
