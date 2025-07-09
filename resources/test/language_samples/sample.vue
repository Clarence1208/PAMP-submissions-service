<template>
  <!-- Vue 3 Sample Component - Task Management Dashboard -->
  <!-- This component demonstrates various Vue.js features including: -->
  <!-- - Composition API with reactive data -->
  <!-- - Computed properties and watchers -->
  <!-- - Component composition and communication -->
  <!-- - Custom directives and plugins -->
  <!-- - Lifecycle hooks and async operations -->
  <!-- - Form handling and validation -->
  <!-- - Transitions and animations -->

  <div class="task-dashboard" :class="{ 'dark-mode': isDarkMode }">
    <!-- Header with navigation and controls -->
    <header class="dashboard-header">
      <div class="header-content">
        <h1 class="dashboard-title">
          <transition name="fade" mode="out-in">
            <span :key="title">{{ title }}</span>
          </transition>
        </h1>
        
        <div class="header-controls">
          <div class="search-container">
            <input
              v-model="searchQuery"
              v-focus
              type="text"
              placeholder="Search tasks..."
              class="search-input"
              @input="handleSearch"
            />
            <i class="search-icon">🔍</i>
          </div>
          
          <select v-model="selectedFilter" class="filter-select">
            <option value="all">All Tasks</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
          
          <button
            @click="toggleDarkMode"
            class="theme-toggle"
            :aria-label="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            {{ isDarkMode ? '☀️' : '🌙' }}
          </button>
          
          <button
            @click="showCreateModal = true"
            class="create-btn"
            :disabled="isLoading"
          >
            <i class="plus-icon">+</i>
            New Task
          </button>
        </div>
      </div>
    </header>

    <!-- Statistics Cards -->
    <section class="stats-section">
      <transition-group name="slide-up" tag="div" class="stats-grid">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="stat-card"
          :class="`stat-${stat.type}`"
        >
          <div class="stat-icon">{{ stat.icon }}</div>
          <div class="stat-content">
            <h3 class="stat-label">{{ stat.label }}</h3>
            <div class="stat-value">
              <animated-number :value="stat.value" />
            </div>
            <div class="stat-change" :class="stat.changeType">
              {{ stat.change }}
            </div>
          </div>
        </div>
      </transition-group>
    </section>

    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Task Filters and Sort Options -->
      <div class="task-controls">
        <div class="filter-tabs">
          <button
            v-for="filter in taskFilters"
            :key="filter.value"
            @click="selectedFilter = filter.value"
            class="filter-tab"
            :class="{ active: selectedFilter === filter.value }"
          >
            {{ filter.label }}
            <span class="task-count">{{ getFilteredTaskCount(filter.value) }}</span>
          </button>
        </div>
        
        <div class="sort-controls">
          <label for="sort-select">Sort by:</label>
          <select id="sort-select" v-model="sortBy" class="sort-select">
            <option value="createdAt">Created Date</option>
            <option value="dueDate">Due Date</option>
            <option value="priority">Priority</option>
            <option value="title">Title</option>
          </select>
          
          <button
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            class="sort-order-btn"
            :aria-label="`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`"
          >
            {{ sortOrder === 'asc' ? '↑' : '↓' }}
          </button>
        </div>
      </div>

      <!-- Task List -->
      <div class="task-list-container">
        <transition name="fade">
          <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading tasks...</p>
          </div>
        </transition>

        <transition name="fade">
          <div v-if="!isLoading && filteredTasks.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <h3>No tasks found</h3>
            <p>{{ searchQuery ? 'Try adjusting your search criteria' : 'Create your first task to get started' }}</p>
            <button @click="showCreateModal = true" class="create-first-task-btn">
              Create Task
            </button>
          </div>
        </transition>

        <transition-group
          v-if="!isLoading && filteredTasks.length > 0"
          name="task-list"
          tag="div"
          class="task-list"
        >
          <task-item
            v-for="task in paginatedTasks"
            :key="task.id"
            :task="task"
            :is-selected="selectedTasks.includes(task.id)"
            @update="handleTaskUpdate"
            @delete="handleTaskDelete"
            @select="handleTaskSelect"
            @toggle-complete="handleTaskToggleComplete"
          />
        </transition-group>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage === 1"
          class="page-btn"
        >
          Previous
        </button>
        
        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="currentPage = page"
            class="page-btn"
            :class="{ active: currentPage === page }"
          >
            {{ page }}
          </button>
        </div>
        
        <button
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="page-btn"
        >
          Next
        </button>
      </div>
    </main>

    <!-- Bulk Actions Bar -->
    <transition name="slide-up">
      <div v-if="selectedTasks.length > 0" class="bulk-actions">
        <div class="bulk-info">
          {{ selectedTasks.length }} task{{ selectedTasks.length === 1 ? '' : 's' }} selected
        </div>
        <div class="bulk-buttons">
          <button @click="bulkComplete" class="bulk-btn complete">
            ✓ Mark Complete
          </button>
          <button @click="bulkDelete" class="bulk-btn delete">
            🗑 Delete
          </button>
          <button @click="selectedTasks = []" class="bulk-btn cancel">
            Cancel
          </button>
        </div>
      </div>
    </transition>

    <!-- Create/Edit Task Modal -->
    <teleport to="body">
      <task-modal
        v-if="showCreateModal || editingTask"
        :task="editingTask"
        :is-editing="!!editingTask"
        @save="handleTaskSave"
        @cancel="handleModalCancel"
      />
    </teleport>

    <!-- Notifications -->
    <notification-container />
  </div>
</template>

<script setup lang="ts">
import { 
  ref, 
  computed, 
  watch, 
  onMounted, 
  onUnmounted, 
  nextTick,
  provide,
  reactive,
  toRefs
} from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useLocalStorage, useDebounce, useAsyncState } from '@/composables'
import TaskItem from '@/components/TaskItem.vue'
import TaskModal from '@/components/TaskModal.vue'
import NotificationContainer from '@/components/NotificationContainer.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'

// Types
interface Task {
  id: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  dueDate?: Date
  createdAt: Date
  updatedAt: Date
  assignee?: string
  tags: string[]
  estimatedHours?: number
  actualHours?: number
}

interface TaskFilter {
  label: string
  value: string
}

interface Stat {
  label: string
  value: number
  icon: string
  type: string
  change: string
  changeType: 'positive' | 'negative' | 'neutral'
}

// Props
interface Props {
  title?: string
  initialFilter?: string
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Task Dashboard',
  initialFilter: 'all',
  pageSize: 10
})

// Emits
const emit = defineEmits<{
  taskCreated: [task: Task]
  taskUpdated: [task: Task]
  taskDeleted: [taskId: string]
  filterChanged: [filter: string]
}>()

// Stores
const taskStore = useTaskStore()
const notificationStore = useNotificationStore()

// Reactive state
const state = reactive({
  searchQuery: '',
  selectedFilter: props.initialFilter,
  sortBy: 'createdAt',
  sortOrder: 'desc' as 'asc' | 'desc',
  currentPage: 1,
  selectedTasks: [] as string[],
  showCreateModal: false,
  editingTask: null as Task | null,
  isLoading: false
})

// Convert reactive state to refs for easier access
const {
  searchQuery,
  selectedFilter,
  sortBy,
  sortOrder,
  currentPage,
  selectedTasks,
  showCreateModal,
  editingTask,
  isLoading
} = toRefs(state)

// Local storage for theme preference
const isDarkMode = useLocalStorage('isDarkMode', false)

// Debounced search
const debouncedSearchQuery = useDebounce(searchQuery, 300)

// Async state for data fetching
const {
  state: tasks,
  isLoading: tasksLoading,
  error: tasksError,
  execute: refreshTasks
} = useAsyncState(
  () => taskStore.fetchTasks(),
  [],
  { immediate: true }
)

// Computed properties
const taskFilters = computed<TaskFilter[]>(() => [
  { label: 'All', value: 'all' },
  { label: 'To Do', value: 'todo' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Completed', value: 'completed' }
])

const filteredTasks = computed(() => {
  let filtered = tasks.value || []

  // Apply search filter
  if (debouncedSearchQuery.value) {
    const query = debouncedSearchQuery.value.toLowerCase()
    filtered = filtered.filter(task =>
      task.title.toLowerCase().includes(query) ||
      task.description?.toLowerCase().includes(query) ||
      task.tags.some(tag => tag.toLowerCase().includes(query))
    )
  }

  // Apply status filter
  if (selectedFilter.value !== 'all') {
    filtered = filtered.filter(task => task.status === selectedFilter.value)
  }

  // Apply sorting
  filtered.sort((a, b) => {
    let aValue: any = a[sortBy.value as keyof Task]
    let bValue: any = b[sortBy.value as keyof Task]

    // Handle date sorting
    if (aValue instanceof Date) aValue = aValue.getTime()
    if (bValue instanceof Date) bValue = bValue.getTime()

    // Handle priority sorting
    if (sortBy.value === 'priority') {
      const priorityOrder = { low: 1, medium: 2, high: 3, urgent: 4 }
      aValue = priorityOrder[aValue as keyof typeof priorityOrder]
      bValue = priorityOrder[bValue as keyof typeof priorityOrder]
    }

    if (aValue < bValue) return sortOrder.value === 'asc' ? -1 : 1
    if (aValue > bValue) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return filtered
})

const paginatedTasks = computed(() => {
  const startIndex = (currentPage.value - 1) * props.pageSize
  const endIndex = startIndex + props.pageSize
  return filteredTasks.value.slice(startIndex, endIndex)
})

const totalPages = computed(() => 
  Math.ceil(filteredTasks.value.length / props.pageSize)
)

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  const half = Math.floor(maxVisible / 2)
  
  let start = Math.max(1, currentPage.value - half)
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

const stats = computed<Stat[]>(() => {
  const allTasks = tasks.value || []
  const total = allTasks.length
  const completed = allTasks.filter(t => t.status === 'completed').length
  const inProgress = allTasks.filter(t => t.status === 'in_progress').length
  const overdue = allTasks.filter(t => 
    t.dueDate && new Date(t.dueDate) < new Date() && t.status !== 'completed'
  ).length

  return [
    {
      label: 'Total Tasks',
      value: total,
      icon: '📋',
      type: 'total',
      change: '+5 this week',
      changeType: 'positive'
    },
    {
      label: 'Completed',
      value: completed,
      icon: '✅',
      type: 'completed',
      change: `${total > 0 ? Math.round((completed / total) * 100) : 0}% completion rate`,
      changeType: 'positive'
    },
    {
      label: 'In Progress',
      value: inProgress,
      icon: '⏳',
      type: 'progress',
      change: '+2 since yesterday',
      changeType: 'neutral'
    },
    {
      label: 'Overdue',
      value: overdue,
      icon: '⚠️',
      type: 'overdue',
      change: overdue > 0 ? 'Needs attention' : 'All up to date',
      changeType: overdue > 0 ? 'negative' : 'positive'
    }
  ]
})

// Methods
function getFilteredTaskCount(filterValue: string): number {
  if (filterValue === 'all') return tasks.value?.length || 0
  return tasks.value?.filter(task => task.status === filterValue).length || 0
}

function handleSearch(event: Event): void {
  const target = event.target as HTMLInputElement
  searchQuery.value = target.value
  currentPage.value = 1 // Reset to first page when searching
}

function toggleDarkMode(): void {
  isDarkMode.value = !isDarkMode.value
}

async function handleTaskUpdate(updatedTask: Task): Promise<void> {
  try {
    await taskStore.updateTask(updatedTask.id, updatedTask)
    await refreshTasks()
    notificationStore.addNotification({
      type: 'success',
      message: 'Task updated successfully',
      duration: 3000
    })
    emit('taskUpdated', updatedTask)
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      message: 'Failed to update task',
      duration: 5000
    })
  }
}

async function handleTaskDelete(taskId: string): Promise<void> {
  try {
    await taskStore.deleteTask(taskId)
    await refreshTasks()
    notificationStore.addNotification({
      type: 'success',
      message: 'Task deleted successfully',
      duration: 3000
    })
    emit('taskDeleted', taskId)
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      message: 'Failed to delete task',
      duration: 5000
    })
  }
}

function handleTaskSelect(taskId: string, selected: boolean): void {
  if (selected) {
    selectedTasks.value.push(taskId)
  } else {
    const index = selectedTasks.value.indexOf(taskId)
    if (index > -1) {
      selectedTasks.value.splice(index, 1)
    }
  }
}

async function handleTaskToggleComplete(taskId: string): Promise<void> {
  const task = tasks.value?.find(t => t.id === taskId)
  if (task) {
    const newStatus = task.status === 'completed' ? 'todo' : 'completed'
    await handleTaskUpdate({ ...task, status: newStatus })
  }
}

async function handleTaskSave(taskData: Partial<Task>): Promise<void> {
  try {
    if (editingTask.value) {
      // Update existing task
      await taskStore.updateTask(editingTask.value.id, taskData)
      notificationStore.addNotification({
        type: 'success',
        message: 'Task updated successfully',
        duration: 3000
      })
    } else {
      // Create new task
      const newTask = await taskStore.createTask(taskData)
      notificationStore.addNotification({
        type: 'success',
        message: 'Task created successfully',
        duration: 3000
      })
      emit('taskCreated', newTask)
    }
    
    await refreshTasks()
    handleModalCancel()
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      message: editingTask.value ? 'Failed to update task' : 'Failed to create task',
      duration: 5000
    })
  }
}

function handleModalCancel(): void {
  showCreateModal.value = false
  editingTask.value = null
}

async function bulkComplete(): Promise<void> {
  try {
    isLoading.value = true
    await Promise.all(
      selectedTasks.value.map(taskId => {
        const task = tasks.value?.find(t => t.id === taskId)
        if (task && task.status !== 'completed') {
          return taskStore.updateTask(taskId, { status: 'completed' })
        }
      })
    )
    
    await refreshTasks()
    selectedTasks.value = []
    notificationStore.addNotification({
      type: 'success',
      message: 'Tasks marked as complete',
      duration: 3000
    })
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      message: 'Failed to update tasks',
      duration: 5000
    })
  } finally {
    isLoading.value = false
  }
}

async function bulkDelete(): Promise<void> {
  if (!confirm(`Are you sure you want to delete ${selectedTasks.value.length} tasks?`)) {
    return
  }

  try {
    isLoading.value = true
    await Promise.all(
      selectedTasks.value.map(taskId => taskStore.deleteTask(taskId))
    )
    
    await refreshTasks()
    selectedTasks.value = []
    notificationStore.addNotification({
      type: 'success',
      message: 'Tasks deleted successfully',
      duration: 3000
    })
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      message: 'Failed to delete tasks',
      duration: 5000
    })
  } finally {
    isLoading.value = false
  }
}

// Watchers
watch(selectedFilter, (newFilter) => {
  currentPage.value = 1
  emit('filterChanged', newFilter)
})

watch(debouncedSearchQuery, () => {
  currentPage.value = 1
})

watch(isDarkMode, (darkMode) => {
  document.documentElement.classList.toggle('dark', darkMode)
})

// Lifecycle hooks
onMounted(async () => {
  // Set initial theme
  document.documentElement.classList.toggle('dark', isDarkMode.value)
  
  // Set up keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts)
  
  // Focus search input after component is mounted
  await nextTick()
  const searchInput = document.querySelector('.search-input') as HTMLInputElement
  if (searchInput) {
    searchInput.focus()
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboardShortcuts)
})

// Keyboard shortcuts
function handleKeyboardShortcuts(event: KeyboardEvent): void {
  // Ctrl/Cmd + N: New task
  if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
    event.preventDefault()
    showCreateModal.value = true
  }
  
  // Escape: Close modals or clear selection
  if (event.key === 'Escape') {
    if (showCreateModal.value || editingTask.value) {
      handleModalCancel()
    } else if (selectedTasks.value.length > 0) {
      selectedTasks.value = []
    }
  }
  
  // Ctrl/Cmd + A: Select all visible tasks
  if ((event.ctrlKey || event.metaKey) && event.key === 'a' && !showCreateModal.value) {
    event.preventDefault()
    selectedTasks.value = paginatedTasks.value.map(task => task.id)
  }
}

// Provide theme state to child components
provide('isDarkMode', isDarkMode)

// Custom directive for auto-focus
const vFocus = {
  mounted(el: HTMLElement) {
    el.focus()
  }
}
</script>

<style scoped>
/* Component-specific styles */
.task-dashboard {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.task-dashboard.dark-mode {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --border-color: #404040;
}

.dashboard-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
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

.search-container {
  position: relative;
}

.search-input {
  padding: 0.5rem 2.5rem 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-primary);
  width: 300px;
}

.search-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.theme-toggle {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  cursor: pointer;
  font-size: 1.2rem;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s ease;
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.create-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.stats-section {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: var(--bg-secondary);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem 0;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.stat-change {
  font-size: 0.8rem;
  font-weight: 500;
}

.stat-change.positive { color: #10b981; }
.stat-change.negative { color: #ef4444; }
.stat-change.neutral { color: var(--text-secondary); }

.main-content {
  padding: 0 2rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.task-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-tabs {
  display: flex;
  gap: 0.5rem;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.task-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.125rem 0.375rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-select {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.sort-order-btn {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  font-weight: bold;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.create-first-task-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 1rem;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-primary);
}

.page-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bulk-actions {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.bulk-info {
  font-weight: 600;
  color: var(--text-primary);
}

.bulk-buttons {
  display: flex;
  gap: 0.5rem;
}

.bulk-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.bulk-btn.complete {
  background: #10b981;
  color: white;
}

.bulk-btn.delete {
  background: #ef4444;
  color: white;
}

.bulk-btn.cancel {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.task-list-enter-active, .task-list-leave-active {
  transition: all 0.3s ease;
}

.task-list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.task-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.task-list-move {
  transition: transform 0.3s ease;
}

/* Responsive design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-controls {
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .search-input {
    width: 100%;
    max-width: 200px;
  }

  .task-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-tabs {
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .bulk-actions {
    left: 1rem;
    right: 1rem;
    transform: none;
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-buttons {
    justify-content: center;
  }
}
</style> 