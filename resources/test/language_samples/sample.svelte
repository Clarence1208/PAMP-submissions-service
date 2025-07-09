<script>
  // Svelte Sample Component - Interactive Dashboard
  // Demonstrates various Svelte features including:
  // - Reactive statements and declarations
  // - Component composition and communication
  // - Stores for state management
  // - Event handling and custom events
  // - Transitions and animations
  // - Lifecycle functions
  // - Binding and form handling

  import { onMount, onDestroy, createEventDispatcher, tick } from 'svelte';
  import { writable, derived, readable } from 'svelte/store';
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { scale, slide, fade, fly } from 'svelte/transition';
  import { flip } from 'svelte/animate';

  // Props
  export let title = 'Interactive Dashboard';
  export let theme = 'light';
  export let autoRefresh = true;
  export let refreshInterval = 5000;

  // Event dispatcher for parent communication
  const dispatch = createEventDispatcher();

  // Stores for state management
  const users = writable([]);
  const currentUser = writable(null);
  const notifications = writable([]);
  
  // Derived store for user statistics
  const userStats = derived(users, $users => ({
    total: $users.length,
    active: $users.filter(u => u.status === 'active').length,
    premium: $users.filter(u => u.isPremium).length,
    avgAge: $users.length > 0 ? 
      Math.round($users.reduce((sum, u) => sum + u.age, 0) / $users.length) : 0
  }));

  // Readable store for current time
  const currentTime = readable(new Date(), set => {
    const interval = setInterval(() => set(new Date()), 1000);
    return () => clearInterval(interval);
  });

  // Tweened values for smooth animations
  const progress = tweened(0, {
    duration: 800,
    easing: cubicOut
  });

  const revenue = tweened(0, {
    duration: 1200,
    easing: cubicOut
  });

  // Component state
  let searchTerm = '';
  let selectedCategory = 'all';
  let showModal = false;
  let isLoading = false;
  let newUserForm = {
    name: '',
    email: '',
    age: '',
    department: '',
    isPremium: false
  };

  // Reactive declarations
  $: filteredUsers = $users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || user.department === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  $: departments = [...new Set($users.map(u => u.department))];
  
  $: totalRevenue = $users.reduce((sum, user) => 
    sum + (user.isPremium ? 99.99 : 29.99), 0);

  $: {
    // Reactive statement - updates revenue animation when users change
    revenue.set(totalRevenue);
  }

  // Update progress based on active users
  $: {
    if ($userStats.total > 0) {
      progress.set(($userStats.active / $userStats.total) * 100);
    }
  }

  // Form validation
  $: isFormValid = newUserForm.name.trim() && 
                   newUserForm.email.includes('@') && 
                   newUserForm.age > 0 && 
                   newUserForm.department.trim();

  // Auto-refresh functionality
  let refreshTimer;
  
  $: if (autoRefresh) {
    clearInterval(refreshTimer);
    refreshTimer = setInterval(loadUsers, refreshInterval);
  } else {
    clearInterval(refreshTimer);
  }

  // Lifecycle functions
  onMount(async () => {
    console.log('Dashboard component mounted');
    await loadUsers();
    dispatch('mounted', { component: 'dashboard' });
  });

  onDestroy(() => {
    clearInterval(refreshTimer);
    console.log('Dashboard component destroyed');
  });

  // Functions
  async function loadUsers() {
    isLoading = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const sampleUsers = [
        { id: 1, name: 'Alice Johnson', email: 'alice@company.com', age: 28, department: 'Engineering', status: 'active', isPremium: true },
        { id: 2, name: 'Bob Smith', email: 'bob@company.com', age: 35, department: 'Sales', status: 'active', isPremium: false },
        { id: 3, name: 'Carol Williams', email: 'carol@company.com', age: 42, department: 'Marketing', status: 'inactive', isPremium: true },
        { id: 4, name: 'David Brown', email: 'david@company.com', age: 31, department: 'Engineering', status: 'active', isPremium: false },
        { id: 5, name: 'Eva Davis', email: 'eva@company.com', age: 29, department: 'Design', status: 'active', isPremium: true }
      ];
      
      users.set(sampleUsers);
      addNotification('Users loaded successfully', 'success');
    } catch (error) {
      addNotification('Failed to load users', 'error');
    } finally {
      isLoading = false;
    }
  }

  function addUser() {
    if (!isFormValid) return;
    
    const newUser = {
      id: Date.now(),
      name: newUserForm.name,
      email: newUserForm.email,
      age: parseInt(newUserForm.age),
      department: newUserForm.department,
      status: 'active',
      isPremium: newUserForm.isPremium
    };
    
    users.update(currentUsers => [...currentUsers, newUser]);
    
    // Reset form
    newUserForm = {
      name: '',
      email: '',
      age: '',
      department: '',
      isPremium: false
    };
    
    showModal = false;
    addNotification(`User ${newUser.name} added successfully`, 'success');
    dispatch('userAdded', newUser);
  }

  function deleteUser(id) {
    users.update(currentUsers => currentUsers.filter(u => u.id !== id));
    addNotification('User deleted', 'info');
  }

  function toggleUserStatus(id) {
    users.update(currentUsers => 
      currentUsers.map(user => 
        user.id === id 
          ? { ...user, status: user.status === 'active' ? 'inactive' : 'active' }
          : user
      )
    );
  }

  function addNotification(message, type = 'info') {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    
    notifications.update(current => [notification, ...current]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      notifications.update(current => current.filter(n => n.id !== notification.id));
    }, 5000);
  }

  async function handleSearch(event) {
    searchTerm = event.target.value;
    // Add a small delay for better UX
    await tick();
  }

  function exportData() {
    const data = JSON.stringify($users, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'users-export.json';
    a.click();
    
    URL.revokeObjectURL(url);
    addNotification('Data exported successfully', 'success');
  }

  // Custom transition
  function typewriter(node, { speed = 1 }) {
    const valid = node.childNodes.length === 1 && node.childNodes[0].nodeType === Node.TEXT_NODE;
    
    if (!valid) {
      throw new Error(`This transition only works on elements with a single text node child`);
    }
    
    const text = node.textContent;
    const duration = text.length / (speed * 0.01);
    
    return {
      duration,
      tick: t => {
        const i = Math.trunc(text.length * t);
        node.textContent = text.slice(0, i);
      }
    };
  }
</script>

<!-- Main Dashboard Template -->
<div class="dashboard" class:dark={theme === 'dark'}>
  <!-- Header -->
  <header class="header" in:slide>
    <h1 in:typewriter={{ speed: 2 }}>{title}</h1>
    <div class="header-controls">
      <div class="time">
        {$currentTime.toLocaleTimeString()}
      </div>
      <label class="toggle">
        <input type="checkbox" bind:checked={autoRefresh} />
        Auto Refresh
      </label>
      <button class="btn btn-primary" on:click={() => showModal = true}>
        Add User
      </button>
    </div>
  </header>

  <!-- Statistics Cards -->
  <div class="stats-grid" in:fade={{ delay: 200 }}>
    <div class="stat-card" in:fly={{ y: 20, delay: 100 }}>
      <h3>Total Users</h3>
      <div class="stat-value">{$userStats.total}</div>
    </div>
    
    <div class="stat-card" in:fly={{ y: 20, delay: 200 }}>
      <h3>Active Users</h3>
      <div class="stat-value">{$userStats.active}</div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: {$progress}%"></div>
      </div>
    </div>
    
    <div class="stat-card" in:fly={{ y: 20, delay: 300 }}>
      <h3>Premium Users</h3>
      <div class="stat-value">{$userStats.premium}</div>
    </div>
    
    <div class="stat-card" in:fly={{ y: 20, delay: 400 }}>
      <h3>Revenue</h3>
      <div class="stat-value">${$revenue.toFixed(2)}</div>
    </div>
  </div>

  <!-- Filters and Search -->
  <div class="filters" in:slide={{ delay: 300 }}>
    <input 
      type="text" 
      placeholder="Search users..." 
      bind:value={searchTerm}
      on:input={handleSearch}
      class="search-input"
    />
    
    <select bind:value={selectedCategory} class="category-select">
      <option value="all">All Departments</option>
      {#each departments as dept}
        <option value={dept}>{dept}</option>
      {/each}
    </select>
    
    <button class="btn btn-secondary" on:click={loadUsers} disabled={isLoading}>
      {isLoading ? 'Loading...' : 'Refresh'}
    </button>
    
    <button class="btn btn-secondary" on:click={exportData}>
      Export Data
    </button>
  </div>

  <!-- Users List -->
  <div class="users-container">
    {#if isLoading}
      <div class="loading" in:fade>
        <div class="spinner"></div>
        Loading users...
      </div>
    {:else if filteredUsers.length === 0}
      <div class="empty-state" in:fade>
        <p>No users found matching your criteria.</p>
      </div>
    {:else}
      <div class="users-grid" in:fade>
        {#each filteredUsers as user (user.id)}
          <div 
            class="user-card" 
            class:inactive={user.status === 'inactive'}
            in:scale={{ delay: 100 }}
            out:scale={{ duration: 200 }}
            animate:flip={{ duration: 300 }}
          >
            <div class="user-header">
              <h4>{user.name}</h4>
              {#if user.isPremium}
                <span class="premium-badge" in:scale>Premium</span>
              {/if}
            </div>
            
            <p class="user-email">{user.email}</p>
            <p class="user-details">
              Age: {user.age} | {user.department}
            </p>
            
            <div class="user-status">
              Status: 
              <span class="status-indicator" class:active={user.status === 'active'}>
                {user.status}
              </span>
            </div>
            
            <div class="user-actions">
              <button 
                class="btn btn-small" 
                on:click={() => toggleUserStatus(user.id)}
              >
                {user.status === 'active' ? 'Deactivate' : 'Activate'}
              </button>
              
              <button 
                class="btn btn-small btn-danger" 
                on:click={() => deleteUser(user.id)}
              >
                Delete
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Notifications -->
  <div class="notifications">
    {#each $notifications as notification (notification.id)}
      <div 
        class="notification"
        class:success={notification.type === 'success'}
        class:error={notification.type === 'error'}
        class:info={notification.type === 'info'}
        in:fly={{ x: 300, duration: 300 }}
        out:fly={{ x: 300, duration: 200 }}
      >
        <span>{notification.message}</span>
        <button 
          class="close-btn" 
          on:click={() => notifications.update(current => 
            current.filter(n => n.id !== notification.id)
          )}
        >
          ×
        </button>
      </div>
    {/each}
  </div>
</div>

<!-- Modal for Adding Users -->
{#if showModal}
  <div class="modal-backdrop" in:fade out:fade on:click={() => showModal = false}>
    <div class="modal" in:scale out:scale on:click|stopPropagation>
      <div class="modal-header">
        <h3>Add New User</h3>
        <button class="close-btn" on:click={() => showModal = false}>×</button>
      </div>
      
      <form class="modal-body" on:submit|preventDefault={addUser}>
        <div class="form-group">
          <label for="name">Name</label>
          <input 
            id="name"
            type="text" 
            bind:value={newUserForm.name}
            required
          />
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input 
            id="email"
            type="email" 
            bind:value={newUserForm.email}
            required
          />
        </div>
        
        <div class="form-group">
          <label for="age">Age</label>
          <input 
            id="age"
            type="number" 
            bind:value={newUserForm.age}
            min="18" 
            max="100"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="department">Department</label>
          <select id="department" bind:value={newUserForm.department} required>
            <option value="">Select Department</option>
            <option value="Engineering">Engineering</option>
            <option value="Sales">Sales</option>
            <option value="Marketing">Marketing</option>
            <option value="Design">Design</option>
            <option value="HR">HR</option>
          </select>
        </div>
        
        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              bind:checked={newUserForm.isPremium}
            />
            Premium User
          </label>
        </div>
        
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" on:click={() => showModal = false}>
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" disabled={!isFormValid}>
            Add User
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  /* Global Dashboard Styles */
  .dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-color, #f8f9fa);
    color: var(--text-color, #333);
    transition: all 0.3s ease;
  }

  .dashboard.dark {
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --card-bg: #2d2d2d;
    --border-color: #404040;
  }

  /* Header Styles */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--border-color, #e0e0e0);
  }

  .header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .time {
    font-family: 'Courier New', monospace;
    font-weight: bold;
    padding: 0.5rem 1rem;
    background: var(--card-bg, #fff);
    border-radius: 8px;
    border: 1px solid var(--border-color, #e0e0e0);
  }

  /* Statistics Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--card-bg, #fff);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color, #e0e0e0);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  }

  .stat-card h3 {
    margin: 0 0 0.5rem 0;
    color: var(--text-color, #666);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: var(--text-color, #333);
    margin-bottom: 0.5rem;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--border-color, #e0e0e0);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }

  /* Filters */
  .filters {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  .search-input, .category-select {
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 8px;
    background: var(--card-bg, #fff);
    color: var(--text-color, #333);
    font-size: 1rem;
  }

  .search-input {
    flex: 1;
    min-width: 200px;
  }

  /* Buttons */
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: var(--card-bg, #fff);
    color: var(--text-color, #333);
    border: 1px solid var(--border-color, #e0e0e0);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--border-color, #f0f0f0);
  }

  .btn-danger {
    background: #ff4757;
    color: white;
  }

  .btn-small {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Users Grid */
  .users-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .user-card {
    background: var(--card-bg, #fff);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color, #e0e0e0);
    transition: all 0.2s ease;
  }

  .user-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }

  .user-card.inactive {
    opacity: 0.7;
    border-left: 4px solid #ff4757;
  }

  .user-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .user-header h4 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
  }

  .premium-badge {
    background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
    color: #333;
    padding: 0.25rem 0.5rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: bold;
    text-transform: uppercase;
  }

  .user-email {
    color: var(--text-color, #666);
    margin: 0.5rem 0;
    font-size: 0.9rem;
  }

  .user-details {
    margin: 0.5rem 0;
    font-size: 0.9rem;
  }

  .user-status {
    margin: 1rem 0;
    font-size: 0.9rem;
  }

  .status-indicator {
    padding: 0.25rem 0.5rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
    background: #ff4757;
    color: white;
  }

  .status-indicator.active {
    background: #2ed573;
  }

  .user-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  /* Loading and Empty States */
  .loading, .empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-color, #666);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color, #e0e0e0);
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Modal Styles */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: var(--card-bg, #fff);
    border-radius: 12px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
  }

  .modal-header h3 {
    margin: 0;
    font-size: 1.5rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-color, #666);
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-body {
    padding: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--text-color, #333);
  }

  .form-group input, .form-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 8px;
    background: var(--card-bg, #fff);
    color: var(--text-color, #333);
    font-size: 1rem;
  }

  .checkbox-group {
    display: flex;
    align-items: center;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    cursor: pointer;
  }

  .checkbox-label input {
    width: auto;
    margin-right: 0.5rem;
  }

  .modal-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color, #e0e0e0);
  }

  /* Notifications */
  .notifications {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1001;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .notification {
    background: var(--card-bg, #fff);
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 300px;
    max-width: 400px;
  }

  .notification.success {
    border-left: 4px solid #2ed573;
  }

  .notification.error {
    border-left: 4px solid #ff4757;
  }

  .notification.info {
    border-left: 4px solid #667eea;
  }

  /* Toggle Switch */
  .toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    user-select: none;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .dashboard {
      padding: 1rem;
    }

    .header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .header-controls {
      flex-wrap: wrap;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .filters {
      flex-direction: column;
    }

    .users-grid {
      grid-template-columns: 1fr;
    }

    .user-actions {
      flex-direction: column;
    }
  }
</style> 