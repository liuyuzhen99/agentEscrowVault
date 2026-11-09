// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {AgentVault} from "../src/AgentVault.sol";
import {AgentEscrow} from "../src/AgentEscrow.sol";

interface VmDeploy {
    function envAddress(string calldata name) external view returns (address);
    function envOr(string calldata name, address defaultValue) external view returns (address);
    function envUint(string calldata name) external view returns (uint256);
    function startBroadcast(uint256 privateKey) external;
    function stopBroadcast() external;
}

contract DeployScript {
    VmDeploy private constant vm = VmDeploy(address(uint160(uint256(keccak256("hevm cheat code")))));

    function run() external returns (AgentVault vault, AgentEscrow escrow) {
        uint256 deployerKey = vm.envUint("OWNER_PRIVATE_KEY");
        address usdcAddress = vm.envAddress("USDC_ADDRESS");
        address sessionKey = vm.envAddress("AGENT_SESSION_ADDRESS");
        address evaluatorAddress = vm.envOr("EVALUATOR_ADDRESS", address(0));

        vm.startBroadcast(deployerKey);
        vault = new AgentVault(usdcAddress, sessionKey);
        escrow = new AgentEscrow(usdcAddress);
        vault.setEscrowApproved(address(escrow), true);
        if (evaluatorAddress != address(0)) {
            vault.setEvaluatorApproved(evaluatorAddress, true);
        }
        vm.stopBroadcast();
    }
}
