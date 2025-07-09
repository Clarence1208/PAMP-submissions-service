// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Solidity Sample Smart Contract
 * @dev Demonstrates various Solidity features including:
 * - Contract inheritance and interfaces
 * - Events and modifiers
 * - State variables and functions
 * - Error handling and custom errors
 * - Structs, enums, and mappings
 * - Access control and security patterns
 */

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

// Interface for token functionality
interface IERC20Basic {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    
    event Transfer(address indexed from, address indexed to, uint256 value);
}

// Abstract contract for common functionality
abstract contract Pausable {
    bool private _paused;
    
    event Paused(address account);
    event Unpaused(address account);
    
    modifier whenNotPaused() {
        require(!_paused, "Contract is paused");
        _;
    }
    
    modifier whenPaused() {
        require(_paused, "Contract is not paused");
        _;
    }
    
    function paused() public view returns (bool) {
        return _paused;
    }
    
    function _pause() internal virtual whenNotPaused {
        _paused = true;
        emit Paused(msg.sender);
    }
    
    function _unpause() internal virtual whenPaused {
        _paused = false;
        emit Unpaused(msg.sender);
    }
}

// Library for utility functions
library MathUtils {
    using SafeMath for uint256;
    
    function percentage(uint256 amount, uint256 percent) internal pure returns (uint256) {
        return amount.mul(percent).div(100);
    }
    
    function compound(uint256 principal, uint256 rate, uint256 time) internal pure returns (uint256) {
        uint256 factor = 100 + rate;
        uint256 result = principal;
        
        for (uint256 i = 0; i < time; i++) {
            result = result.mul(factor).div(100);
        }
        
        return result;
    }
}

// Custom errors (Solidity 0.8.4+)
error InsufficientBalance(uint256 requested, uint256 available);
error InvalidAddress(address addr);
error TransferFailed();

/**
 * @title Sample Token Contract
 * @dev Implementation of a basic token with additional features
 */
contract SampleToken is IERC20Basic, Ownable, Pausable, ReentrancyGuard {
    using SafeMath for uint256;
    using MathUtils for uint256;
    
    // State variables
    string public name = "Sample Token";
    string public symbol = "SAMPLE";
    uint8 public decimals = 18;
    uint256 private _totalSupply;
    
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    mapping(address => bool) public blacklisted;
    
    // Structs
    struct UserInfo {
        uint256 balance;
        uint256 lastTransactionTime;
        bool isVIP;
        uint256 totalTransactions;
    }
    
    mapping(address => UserInfo) public userInfo;
    
    // Enums
    enum TransactionType { TRANSFER, MINT, BURN, STAKE }
    
    struct Transaction {
        address from;
        address to;
        uint256 amount;
        TransactionType txType;
        uint256 timestamp;
    }
    
    Transaction[] public transactionHistory;
    
    // Events
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);
    event BlacklistUpdated(address indexed account, bool isBlacklisted);
    event VIPStatusUpdated(address indexed account, bool isVIP);
    
    // Modifiers
    modifier validAddress(address _addr) {
        if (_addr == address(0)) {
            revert InvalidAddress(_addr);
        }
        _;
    }
    
    modifier notBlacklisted(address _addr) {
        require(!blacklisted[_addr], "Address is blacklisted");
        _;
    }
    
    modifier onlyVIP() {
        require(userInfo[msg.sender].isVIP, "VIP access required");
        _;
    }
    
    /**
     * @dev Constructor that gives msg.sender all of existing tokens
     */
    constructor(uint256 _initialSupply) {
        _totalSupply = _initialSupply * 10**decimals;
        _balances[msg.sender] = _totalSupply;
        
        userInfo[msg.sender] = UserInfo({
            balance: _totalSupply,
            lastTransactionTime: block.timestamp,
            isVIP: true,
            totalTransactions: 0
        });
        
        emit Transfer(address(0), msg.sender, _totalSupply);
    }
    
    /**
     * @dev Returns the total supply of tokens
     */
    function totalSupply() public view override returns (uint256) {
        return _totalSupply;
    }
    
    /**
     * @dev Returns the balance of a specific account
     */
    function balanceOf(address account) public view override returns (uint256) {
        return _balances[account];
    }
    
    /**
     * @dev Transfer tokens to a specified address
     */
    function transfer(address recipient, uint256 amount) 
        public 
        override 
        validAddress(recipient)
        notBlacklisted(msg.sender)
        notBlacklisted(recipient)
        whenNotPaused
        nonReentrant
        returns (bool) 
    {
        _transfer(msg.sender, recipient, amount);
        return true;
    }
    
    /**
     * @dev Internal transfer function
     */
    function _transfer(address sender, address recipient, uint256 amount) internal {
        if (_balances[sender] < amount) {
            revert InsufficientBalance(amount, _balances[sender]);
        }
        
        _balances[sender] = _balances[sender].sub(amount);
        _balances[recipient] = _balances[recipient].add(amount);
        
        // Update user info
        userInfo[sender].balance = _balances[sender];
        userInfo[sender].lastTransactionTime = block.timestamp;
        userInfo[sender].totalTransactions++;
        
        userInfo[recipient].balance = _balances[recipient];
        userInfo[recipient].lastTransactionTime = block.timestamp;
        userInfo[recipient].totalTransactions++;
        
        // Record transaction
        transactionHistory.push(Transaction({
            from: sender,
            to: recipient,
            amount: amount,
            txType: TransactionType.TRANSFER,
            timestamp: block.timestamp
        }));
        
        emit Transfer(sender, recipient, amount);
    }
    
    /**
     * @dev Mint new tokens (only owner)
     */
    function mint(address to, uint256 amount) 
        public 
        onlyOwner 
        validAddress(to) 
        whenNotPaused 
    {
        _totalSupply = _totalSupply.add(amount);
        _balances[to] = _balances[to].add(amount);
        
        userInfo[to].balance = _balances[to];
        userInfo[to].lastTransactionTime = block.timestamp;
        
        transactionHistory.push(Transaction({
            from: address(0),
            to: to,
            amount: amount,
            txType: TransactionType.MINT,
            timestamp: block.timestamp
        }));
        
        emit Mint(to, amount);
        emit Transfer(address(0), to, amount);
    }
    
    /**
     * @dev Burn tokens from sender's account
     */
    function burn(uint256 amount) public whenNotPaused {
        if (_balances[msg.sender] < amount) {
            revert InsufficientBalance(amount, _balances[msg.sender]);
        }
        
        _balances[msg.sender] = _balances[msg.sender].sub(amount);
        _totalSupply = _totalSupply.sub(amount);
        
        userInfo[msg.sender].balance = _balances[msg.sender];
        userInfo[msg.sender].lastTransactionTime = block.timestamp;
        
        transactionHistory.push(Transaction({
            from: msg.sender,
            to: address(0),
            amount: amount,
            txType: TransactionType.BURN,
            timestamp: block.timestamp
        }));
        
        emit Burn(msg.sender, amount);
        emit Transfer(msg.sender, address(0), amount);
    }
    
    /**
     * @dev Update blacklist status (only owner)
     */
    function updateBlacklist(address account, bool isBlacklisted) 
        public 
        onlyOwner 
        validAddress(account) 
    {
        blacklisted[account] = isBlacklisted;
        emit BlacklistUpdated(account, isBlacklisted);
    }
    
    /**
     * @dev Update VIP status (only owner)
     */
    function updateVIPStatus(address account, bool isVIP) 
        public 
        onlyOwner 
        validAddress(account) 
    {
        userInfo[account].isVIP = isVIP;
        emit VIPStatusUpdated(account, isVIP);
    }
    
    /**
     * @dev Pause the contract (only owner)
     */
    function pause() public onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause the contract (only owner)
     */
    function unpause() public onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Get transaction count
     */
    function getTransactionCount() public view returns (uint256) {
        return transactionHistory.length;
    }
    
    /**
     * @dev Get transaction by index
     */
    function getTransaction(uint256 index) 
        public 
        view 
        returns (
            address from,
            address to,
            uint256 amount,
            TransactionType txType,
            uint256 timestamp
        ) 
    {
        require(index < transactionHistory.length, "Transaction index out of bounds");
        
        Transaction memory txn = transactionHistory[index];
        return (txn.from, txn.to, txn.amount, txn.txType, txn.timestamp);
    }
    
    /**
     * @dev Calculate compound interest for VIP users
     */
    function calculateVIPBonus(uint256 amount) public view onlyVIP returns (uint256) {
        return amount.compound(5, 1); // 5% bonus for VIP users
    }
    
    /**
     * @dev Batch transfer to multiple recipients (VIP only)
     */
    function batchTransfer(address[] memory recipients, uint256[] memory amounts) 
        public 
        onlyVIP 
        whenNotPaused 
        nonReentrant 
    {
        require(recipients.length == amounts.length, "Arrays length mismatch");
        require(recipients.length <= 100, "Too many recipients");
        
        uint256 totalAmount = 0;
        for (uint256 i = 0; i < amounts.length; i++) {
            totalAmount = totalAmount.add(amounts[i]);
        }
        
        if (_balances[msg.sender] < totalAmount) {
            revert InsufficientBalance(totalAmount, _balances[msg.sender]);
        }
        
        for (uint256 i = 0; i < recipients.length; i++) {
            if (recipients[i] != address(0) && !blacklisted[recipients[i]]) {
                _transfer(msg.sender, recipients[i], amounts[i]);
            }
        }
    }
    
    /**
     * @dev Emergency withdraw (only owner, when paused)
     */
    function emergencyWithdraw(address token, uint256 amount) 
        public 
        onlyOwner 
        whenPaused 
    {
        if (token == address(0)) {
            // Withdraw ETH
            payable(owner()).transfer(amount);
        } else {
            // Withdraw ERC20 tokens
            IERC20Basic(token).transfer(owner(), amount);
        }
    }
    
    /**
     * @dev Fallback function to receive ETH
     */
    receive() external payable {
        // Can implement ETH staking logic here
    }
    
    /**
     * @dev Get contract info
     */
    function getContractInfo() 
        public 
        view 
        returns (
            string memory tokenName,
            string memory tokenSymbol,
            uint256 tokenTotalSupply,
            uint256 contractBalance,
            bool isPaused
        ) 
    {
        return (
            name,
            symbol,
            _totalSupply,
            address(this).balance,
            paused()
        );
    }
}

/**
 * @title Sample Staking Contract
 * @dev Allows users to stake tokens and earn rewards
 */
contract SampleStaking is Ownable, ReentrancyGuard {
    using SafeMath for uint256;
    
    SampleToken public stakingToken;
    
    struct StakeInfo {
        uint256 amount;
        uint256 startTime;
        uint256 lastRewardTime;
        uint256 rewardDebt;
    }
    
    mapping(address => StakeInfo) public stakes;
    uint256 public totalStaked;
    uint256 public rewardRate = 100; // 1% per day (in basis points)
    
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 reward);
    
    constructor(address _stakingToken) {
        stakingToken = SampleToken(_stakingToken);
    }
    
    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot stake 0 tokens");
        
        // Calculate pending rewards
        uint256 pendingReward = calculateReward(msg.sender);
        
        // Transfer tokens from user to contract
        stakingToken.transfer(address(this), amount);
        
        // Update stake info
        stakes[msg.sender].amount = stakes[msg.sender].amount.add(amount);
        stakes[msg.sender].startTime = block.timestamp;
        stakes[msg.sender].lastRewardTime = block.timestamp;
        stakes[msg.sender].rewardDebt = stakes[msg.sender].rewardDebt.add(pendingReward);
        
        totalStaked = totalStaked.add(amount);
        
        emit Staked(msg.sender, amount);
    }
    
    function unstake(uint256 amount) external nonReentrant {
        require(stakes[msg.sender].amount >= amount, "Insufficient staked amount");
        
        // Calculate and transfer rewards
        uint256 reward = calculateReward(msg.sender);
        if (reward > 0) {
            stakingToken.mint(msg.sender, reward);
            emit RewardClaimed(msg.sender, reward);
        }
        
        // Update stake info
        stakes[msg.sender].amount = stakes[msg.sender].amount.sub(amount);
        stakes[msg.sender].lastRewardTime = block.timestamp;
        stakes[msg.sender].rewardDebt = 0;
        
        totalStaked = totalStaked.sub(amount);
        
        // Transfer staked tokens back to user
        stakingToken.transfer(msg.sender, amount);
        
        emit Unstaked(msg.sender, amount);
    }
    
    function calculateReward(address user) public view returns (uint256) {
        StakeInfo memory userStake = stakes[user];
        if (userStake.amount == 0) {
            return 0;
        }
        
        uint256 stakingDuration = block.timestamp.sub(userStake.lastRewardTime);
        uint256 dailyReward = userStake.amount.mul(rewardRate).div(10000);
        uint256 reward = dailyReward.mul(stakingDuration).div(1 days);
        
        return reward.add(userStake.rewardDebt);
    }
    
    function claimReward() external nonReentrant {
        uint256 reward = calculateReward(msg.sender);
        require(reward > 0, "No rewards to claim");
        
        stakes[msg.sender].lastRewardTime = block.timestamp;
        stakes[msg.sender].rewardDebt = 0;
        
        stakingToken.mint(msg.sender, reward);
        emit RewardClaimed(msg.sender, reward);
    }
} 