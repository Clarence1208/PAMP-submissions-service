// TypeScript Sample Program - Advanced Task Management System
// This program demonstrates various TypeScript features including:
// - Advanced type system with unions, intersections, and mapped types
// - Generic types and constraints
// - Decorators and metadata
// - Modules and namespaces
// - Async/await patterns
// - Class-based and functional programming
// - Error handling with Result types
// - Advanced utility types

import { EventEmitter } from 'events';

// =============================================================================
// UTILITY TYPES AND TYPE ALIASES
// =============================================================================

type ID = string | number;
type Timestamp = number;
type Optional<T> = T | undefined;
type Nullable<T> = T | null;

// Utility type for making specific properties optional
type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Advanced mapped type for deep readonly
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

// Union type with discriminated unions
type ApiResponse<T> = 
  | { status: 'success'; data: T }
  | { status: 'error'; error: string; code: number }
  | { status: 'loading' };

// Template literal types
type EventName<T extends string> = `on${Capitalize<T>}`;
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
type ApiEndpoint = `/api/v1/${string}`;

// =============================================================================
// ENUMS AND CONSTANTS
// =============================================================================

enum TaskStatus {
  TODO = 'todo',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

enum Priority {
  LOW = 1,
  MEDIUM = 2,
  HIGH = 3,
  URGENT = 4
}

const enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

// =============================================================================
// INTERFACES AND TYPES
// =============================================================================

interface BaseEntity {
  readonly id: ID;
  readonly createdAt: Timestamp;
  readonly updatedAt: Timestamp;
}

interface User extends BaseEntity {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  roles: Role[];
  preferences: UserPreferences;
  isActive: boolean;
}

interface Role {
  id: ID;
  name: string;
  permissions: Permission[];
}

interface Permission {
  resource: string;
  action: string;
  conditions?: Record<string, any>;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
}

interface Task extends BaseEntity {
  title: string;
  description?: string;
  status: TaskStatus;
  priority: Priority;
  assigneeId?: ID;
  assignee?: User;
  projectId: ID;
  project?: Project;
  tags: string[];
  dueDate?: Date;
  estimatedHours?: number;
  actualHours?: number;
  dependencies: ID[];
  attachments: Attachment[];
  comments: Comment[];
}

interface Project extends BaseEntity {
  name: string;
  description?: string;
  ownerId: ID;
  owner?: User;
  members: ProjectMember[];
  tasks: Task[];
  settings: ProjectSettings;
  isArchived: boolean;
}

interface ProjectMember {
  userId: ID;
  user?: User;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joinedAt: Timestamp;
}

interface ProjectSettings {
  isPublic: boolean;
  allowGuests: boolean;
  defaultTaskStatus: TaskStatus;
  workflowSteps: WorkflowStep[];
}

interface WorkflowStep {
  id: ID;
  name: string;
  fromStatus: TaskStatus;
  toStatus: TaskStatus;
  conditions?: string[];
}

interface Attachment {
  id: ID;
  filename: string;
  mimeType: string;
  size: number;
  url: string;
  uploadedBy: ID;
  uploadedAt: Timestamp;
}

interface Comment extends BaseEntity {
  content: string;
  authorId: ID;
  author?: User;
  taskId: ID;
  parentId?: ID;
  replies?: Comment[];
  mentions: ID[];
  isEdited: boolean;
}

// =============================================================================
// GENERIC INTERFACES AND CONSTRAINTS
// =============================================================================

interface Repository<T extends BaseEntity> {
  findById(id: ID): Promise<T | null>;
  findAll(options?: QueryOptions): Promise<T[]>;
  create(data: Omit<T, keyof BaseEntity>): Promise<T>;
  update(id: ID, data: Partial<T>): Promise<T>;
  delete(id: ID): Promise<boolean>;
}

interface QueryOptions {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filters?: Record<string, any>;
  include?: string[];
}

interface Service<T extends BaseEntity, TCreate = Omit<T, keyof BaseEntity>, TUpdate = Partial<T>> {
  findById(id: ID): Promise<Result<T, ServiceError>>;
  findAll(options?: QueryOptions): Promise<Result<PaginatedResult<T>, ServiceError>>;
  create(data: TCreate): Promise<Result<T, ServiceError>>;
  update(id: ID, data: TUpdate): Promise<Result<T, ServiceError>>;
  delete(id: ID): Promise<Result<boolean, ServiceError>>;
}

interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Result type for error handling
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

class ServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'ServiceError';
  }
}

// =============================================================================
// DECORATORS
// =============================================================================

// Class decorator
function Entity(tableName: string) {
  return function <T extends new (...args: any[]) => {}>(constructor: T) {
    return class extends constructor {
      static tableName = tableName;
    };
  };
}

// Method decorator for logging
function Log(logLevel: LogLevel = LogLevel.INFO) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    
    descriptor.value = function (...args: any[]) {
      console.log(`[${logLevel.toUpperCase()}] Calling ${propertyName} with args:`, args);
      const result = method.apply(this, args);
      
      if (result instanceof Promise) {
        return result.then((res) => {
          console.log(`[${logLevel.toUpperCase()}] ${propertyName} completed with result:`, res);
          return res;
        }).catch((err) => {
          console.error(`[${logLevel.toUpperCase()}] ${propertyName} failed with error:`, err);
          throw err;
        });
      }
      
      console.log(`[${logLevel.toUpperCase()}] ${propertyName} completed with result:`, result);
      return result;
    };
    
    return descriptor;
  };
}

// Property decorator for validation
function Validate(validator: (value: any) => boolean, message: string) {
  return function (target: any, propertyName: string) {
    let value: any;
    
    const getter = () => value;
    const setter = (newValue: any) => {
      if (!validator(newValue)) {
        throw new Error(`Validation failed for ${propertyName}: ${message}`);
      }
      value = newValue;
    };
    
    Object.defineProperty(target, propertyName, {
      get: getter,
      set: setter,
      enumerable: true,
      configurable: true
    });
  };
}

// =============================================================================
// CLASSES WITH GENERICS AND ADVANCED FEATURES
// =============================================================================

@Entity('tasks')
class TaskEntity implements Task {
  readonly id: ID;
  readonly createdAt: Timestamp;
  readonly updatedAt: Timestamp;
  
  @Validate((value: string) => value.length > 0, 'Title cannot be empty')
  title: string;
  
  description?: string;
  status: TaskStatus;
  priority: Priority;
  assigneeId?: ID;
  assignee?: User;
  projectId: ID;
  project?: Project;
  tags: string[];
  dueDate?: Date;
  estimatedHours?: number;
  actualHours?: number;
  dependencies: ID[];
  attachments: Attachment[];
  comments: Comment[];

  constructor(data: Omit<Task, keyof BaseEntity>) {
    this.id = generateId();
    this.createdAt = Date.now();
    this.updatedAt = Date.now();
    
    Object.assign(this, data);
  }

  @Log(LogLevel.INFO)
  updateStatus(newStatus: TaskStatus): void {
    this.status = newStatus;
    this.updatedAt = Date.now();
  }

  @Log(LogLevel.DEBUG)
  addTag(tag: string): void {
    if (!this.tags.includes(tag)) {
      this.tags.push(tag);
      this.updatedAt = Date.now();
    }
  }

  removeTag(tag: string): void {
    const index = this.tags.indexOf(tag);
    if (index > -1) {
      this.tags.splice(index, 1);
      this.updatedAt = Date.now();
    }
  }

  calculateProgress(): number {
    if (!this.estimatedHours || this.estimatedHours === 0) return 0;
    return Math.min((this.actualHours || 0) / this.estimatedHours, 1) * 100;
  }

  isOverdue(): boolean {
    return this.dueDate ? new Date() > this.dueDate : false;
  }
}

// Generic repository implementation
abstract class BaseRepository<T extends BaseEntity> implements Repository<T> {
  protected abstract tableName: string;
  protected items: Map<ID, T> = new Map();

  async findById(id: ID): Promise<T | null> {
    return this.items.get(id) || null;
  }

  async findAll(options: QueryOptions = {}): Promise<T[]> {
    let items = Array.from(this.items.values());
    
    // Apply filters
    if (options.filters) {
      items = items.filter(item => this.matchesFilters(item, options.filters!));
    }
    
    // Apply sorting
    if (options.sortBy) {
      items.sort((a, b) => this.compareItems(a, b, options.sortBy!, options.sortOrder));
    }
    
    // Apply pagination
    if (options.page && options.limit) {
      const startIndex = (options.page - 1) * options.limit;
      items = items.slice(startIndex, startIndex + options.limit);
    }
    
    return items;
  }

  async create(data: Omit<T, keyof BaseEntity>): Promise<T> {
    const entity = this.createEntity(data);
    this.items.set(entity.id, entity);
    return entity;
  }

  async update(id: ID, data: Partial<T>): Promise<T> {
    const existing = await this.findById(id);
    if (!existing) {
      throw new ServiceError(`Entity with id ${id} not found`, 'NOT_FOUND', 404);
    }
    
    const updated = { ...existing, ...data, updatedAt: Date.now() } as T;
    this.items.set(id, updated);
    return updated;
  }

  async delete(id: ID): Promise<boolean> {
    return this.items.delete(id);
  }

  protected abstract createEntity(data: Omit<T, keyof BaseEntity>): T;

  private matchesFilters(item: T, filters: Record<string, any>): boolean {
    return Object.entries(filters).every(([key, value]) => {
      const itemValue = (item as any)[key];
      return Array.isArray(value) ? value.includes(itemValue) : itemValue === value;
    });
  }

  private compareItems(a: T, b: T, sortBy: string, sortOrder: 'asc' | 'desc' = 'asc'): number {
    const aValue = (a as any)[sortBy];
    const bValue = (b as any)[sortBy];
    
    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  }
}

class TaskRepository extends BaseRepository<Task> {
  protected tableName = 'tasks';

  protected createEntity(data: Omit<Task, keyof BaseEntity>): Task {
    return new TaskEntity(data);
  }

  async findByProject(projectId: ID): Promise<Task[]> {
    return this.findAll({ filters: { projectId } });
  }

  async findByAssignee(assigneeId: ID): Promise<Task[]> {
    return this.findAll({ filters: { assigneeId } });
  }

  async findOverdueTasks(): Promise<Task[]> {
    const allTasks = await this.findAll();
    return allTasks.filter(task => task.dueDate && new Date() > task.dueDate);
  }
}

// =============================================================================
// SERVICE LAYER WITH ASYNC PATTERNS
// =============================================================================

class TaskService implements Service<Task> {
  constructor(
    private taskRepository: TaskRepository,
    private userRepository: Repository<User>,
    private projectRepository: Repository<Project>,
    private eventEmitter: EventEmitter = new EventEmitter()
  ) {}

  async findById(id: ID): Promise<Result<Task, ServiceError>> {
    try {
      const task = await this.taskRepository.findById(id);
      if (!task) {
        return { success: false, error: new ServiceError('Task not found', 'NOT_FOUND', 404) };
      }
      
      // Populate relations
      await this.populateTaskRelations(task);
      
      return { success: true, data: task };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to fetch task', 'FETCH_ERROR') };
    }
  }

  async findAll(options?: QueryOptions): Promise<Result<PaginatedResult<Task>, ServiceError>> {
    try {
      const tasks = await this.taskRepository.findAll(options);
      
      // Populate relations for all tasks
      await Promise.all(tasks.map(task => this.populateTaskRelations(task)));
      
      const total = (await this.taskRepository.findAll()).length;
      const page = options?.page || 1;
      const limit = options?.limit || 10;
      
      const result: PaginatedResult<Task> = {
        data: tasks,
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit)
      };
      
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to fetch tasks', 'FETCH_ERROR') };
    }
  }

  async create(data: Omit<Task, keyof BaseEntity>): Promise<Result<Task, ServiceError>> {
    try {
      // Validate project exists
      const project = await this.projectRepository.findById(data.projectId);
      if (!project) {
        return { success: false, error: new ServiceError('Project not found', 'INVALID_PROJECT', 400) };
      }

      // Validate assignee exists if provided
      if (data.assigneeId) {
        const assignee = await this.userRepository.findById(data.assigneeId);
        if (!assignee) {
          return { success: false, error: new ServiceError('Assignee not found', 'INVALID_ASSIGNEE', 400) };
        }
      }

      const task = await this.taskRepository.create(data);
      await this.populateTaskRelations(task);
      
      // Emit event
      this.eventEmitter.emit('taskCreated', task);
      
      return { success: true, data: task };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to create task', 'CREATE_ERROR') };
    }
  }

  async update(id: ID, data: Partial<Task>): Promise<Result<Task, ServiceError>> {
    try {
      const existingResult = await this.findById(id);
      if (!existingResult.success) {
        return existingResult;
      }

      const task = await this.taskRepository.update(id, data);
      await this.populateTaskRelations(task);
      
      // Emit event
      this.eventEmitter.emit('taskUpdated', task, existingResult.data);
      
      return { success: true, data: task };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to update task', 'UPDATE_ERROR') };
    }
  }

  async delete(id: ID): Promise<Result<boolean, ServiceError>> {
    try {
      const existingResult = await this.findById(id);
      if (!existingResult.success) {
        return existingResult;
      }

      const deleted = await this.taskRepository.delete(id);
      
      if (deleted) {
        this.eventEmitter.emit('taskDeleted', existingResult.data);
      }
      
      return { success: true, data: deleted };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to delete task', 'DELETE_ERROR') };
    }
  }

  // Custom business logic methods
  async assignTask(taskId: ID, assigneeId: ID): Promise<Result<Task, ServiceError>> {
    return this.update(taskId, { assigneeId });
  }

  async updateTaskStatus(taskId: ID, status: TaskStatus): Promise<Result<Task, ServiceError>> {
    return this.update(taskId, { status });
  }

  async addTaskComment(taskId: ID, content: string, authorId: ID): Promise<Result<Comment, ServiceError>> {
    try {
      const taskResult = await this.findById(taskId);
      if (!taskResult.success) {
        return { success: false, error: taskResult.error };
      }

      const comment: Comment = {
        id: generateId(),
        content,
        authorId,
        taskId,
        mentions: this.extractMentions(content),
        isEdited: false,
        createdAt: Date.now(),
        updatedAt: Date.now()
      };

      taskResult.data.comments.push(comment);
      await this.taskRepository.update(taskId, { comments: taskResult.data.comments });
      
      this.eventEmitter.emit('commentAdded', comment, taskResult.data);
      
      return { success: true, data: comment };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to add comment', 'COMMENT_ERROR') };
    }
  }

  async getTasksByProject(projectId: ID): Promise<Result<Task[], ServiceError>> {
    try {
      const tasks = await this.taskRepository.findByProject(projectId);
      await Promise.all(tasks.map(task => this.populateTaskRelations(task)));
      return { success: true, data: tasks };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to fetch project tasks', 'FETCH_ERROR') };
    }
  }

  async getOverdueTasks(): Promise<Result<Task[], ServiceError>> {
    try {
      const tasks = await this.taskRepository.findOverdueTasks();
      await Promise.all(tasks.map(task => this.populateTaskRelations(task)));
      return { success: true, data: tasks };
    } catch (error) {
      return { success: false, error: new ServiceError('Failed to fetch overdue tasks', 'FETCH_ERROR') };
    }
  }

  private async populateTaskRelations(task: Task): Promise<void> {
    if (task.assigneeId) {
      task.assignee = await this.userRepository.findById(task.assigneeId) || undefined;
    }
    
    task.project = await this.projectRepository.findById(task.projectId) || undefined;
  }

  private extractMentions(content: string): ID[] {
    const mentionRegex = /@(\w+)/g;
    const mentions: ID[] = [];
    let match;
    
    while ((match = mentionRegex.exec(content)) !== null) {
      mentions.push(match[1]);
    }
    
    return mentions;
  }
}

// =============================================================================
// FUNCTIONAL PROGRAMMING UTILITIES
// =============================================================================

// Function composition utilities
type Fn<T, U> = (arg: T) => U;

function pipe<T>(...fns: Array<Fn<any, any>>): Fn<T, any> {
  return (value: T) => fns.reduce((acc, fn) => fn(acc), value);
}

function compose<T>(...fns: Array<Fn<any, any>>): Fn<T, any> {
  return (value: T) => fns.reduceRight((acc, fn) => fn(acc), value);
}

// Currying utility
function curry<T, U, V>(fn: (a: T, b: U) => V): (a: T) => (b: U) => V {
  return (a: T) => (b: U) => fn(a, b);
}

// Maybe monad for handling nullable values
class Maybe<T> {
  constructor(private value: T | null | undefined) {}

  static of<T>(value: T): Maybe<T> {
    return new Maybe(value);
  }

  static none<T>(): Maybe<T> {
    return new Maybe<T>(null);
  }

  map<U>(fn: (value: T) => U): Maybe<U> {
    return this.value != null ? Maybe.of(fn(this.value)) : Maybe.none<U>();
  }

  flatMap<U>(fn: (value: T) => Maybe<U>): Maybe<U> {
    return this.value != null ? fn(this.value) : Maybe.none<U>();
  }

  filter(predicate: (value: T) => boolean): Maybe<T> {
    return this.value != null && predicate(this.value) ? this : Maybe.none<T>();
  }

  getOrElse(defaultValue: T): T {
    return this.value != null ? this.value : defaultValue;
  }

  isSome(): boolean {
    return this.value != null;
  }

  isNone(): boolean {
    return this.value == null;
  }
}

// =============================================================================
// ADVANCED TYPE UTILITIES AND HELPERS
// =============================================================================

// Type guards
function isTask(obj: any): obj is Task {
  return obj && typeof obj.id !== 'undefined' && typeof obj.title === 'string';
}

function isUser(obj: any): obj is User {
  return obj && typeof obj.id !== 'undefined' && typeof obj.email === 'string';
}

// Generic type assertion
function assertType<T>(obj: any, typeGuard: (obj: any) => obj is T): T {
  if (!typeGuard(obj)) {
    throw new Error('Type assertion failed');
  }
  return obj;
}

// Conditional types
type NonNullable<T> = T extends null | undefined ? never : T;
type ExtractArrayType<T> = T extends (infer U)[] ? U : never;
type FunctionReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// =============================================================================
// API CLIENT WITH ADVANCED TYPING
// =============================================================================

interface ApiClient {
  get<T>(endpoint: ApiEndpoint): Promise<ApiResponse<T>>;
  post<T, U>(endpoint: ApiEndpoint, data: T): Promise<ApiResponse<U>>;
  put<T, U>(endpoint: ApiEndpoint, data: T): Promise<ApiResponse<U>>;
  delete(endpoint: ApiEndpoint): Promise<ApiResponse<boolean>>;
}

class HttpClient implements ApiClient {
  constructor(private baseUrl: string, private defaultHeaders: Record<string, string> = {}) {}

  async get<T>(endpoint: ApiEndpoint): Promise<ApiResponse<T>> {
    return this.request<T>('GET', endpoint);
  }

  async post<T, U>(endpoint: ApiEndpoint, data: T): Promise<ApiResponse<U>> {
    return this.request<U>('POST', endpoint, data);
  }

  async put<T, U>(endpoint: ApiEndpoint, data: T): Promise<ApiResponse<U>> {
    return this.request<U>('PUT', endpoint, data);
  }

  async delete(endpoint: ApiEndpoint): Promise<ApiResponse<boolean>> {
    return this.request<boolean>('DELETE', endpoint);
  }

  private async request<T>(
    method: HttpMethod,
    endpoint: ApiEndpoint,
    data?: any
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.defaultHeaders
        },
        body: data ? JSON.stringify(data) : undefined
      });

      if (!response.ok) {
        return {
          status: 'error',
          error: `HTTP ${response.status}: ${response.statusText}`,
          code: response.status
        };
      }

      const responseData = await response.json();
      return { status: 'success', data: responseData };
    } catch (error) {
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        code: 500
      };
    }
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// =============================================================================
// EXAMPLE USAGE AND DEMONSTRATION
// =============================================================================

async function demonstrateTaskManagement(): Promise<void> {
  // Create repositories
  const taskRepository = new TaskRepository();
  const userRepository = new BaseRepository<User>() as Repository<User>;
  const projectRepository = new BaseRepository<Project>() as Repository<Project>;
  
  // Create service
  const taskService = new TaskService(taskRepository, userRepository, projectRepository);
  
  // Event listeners
  taskService['eventEmitter'].on('taskCreated', (task: Task) => {
    console.log('New task created:', task.title);
  });
  
  taskService['eventEmitter'].on('taskUpdated', (newTask: Task, oldTask: Task) => {
    console.log(`Task updated: ${oldTask.title} -> ${newTask.title}`);
  });
  
  // Create a new task
  const createResult = await taskService.create({
    title: 'Implement TypeScript sample',
    description: 'Create a comprehensive TypeScript example with advanced features',
    status: TaskStatus.IN_PROGRESS,
    priority: Priority.HIGH,
    projectId: 'project-1',
    tags: ['typescript', 'sample', 'development'],
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days from now
    estimatedHours: 8,
    dependencies: [],
    attachments: [],
    comments: []
  });
  
  if (createResult.success) {
    console.log('Task created successfully:', createResult.data.id);
    
    // Update task status
    const updateResult = await taskService.updateTaskStatus(
      createResult.data.id,
      TaskStatus.COMPLETED
    );
    
    if (updateResult.success) {
      console.log('Task status updated:', updateResult.data.status);
    }
    
    // Add a comment
    const commentResult = await taskService.addTaskComment(
      createResult.data.id,
      'Great work on this implementation! @john @jane',
      'user-1'
    );
    
    if (commentResult.success) {
      console.log('Comment added:', commentResult.data.content);
      console.log('Mentions:', commentResult.data.mentions);
    }
  }
  
  // Demonstrate functional programming
  const processTaskTitle = pipe(
    (title: string) => title.toLowerCase(),
    (title: string) => title.replace(/\s+/g, '-'),
    (title: string) => title.substring(0, 50)
  );
  
  console.log('Processed title:', processTaskTitle('Implement TypeScript Sample'));
  
  // Demonstrate Maybe monad
  const maybeTask = Maybe.of(createResult.success ? createResult.data : null);
  const taskTitle = maybeTask
    .map(task => task.title)
    .filter(title => title.length > 0)
    .getOrElse('No title');
  
  console.log('Task title from Maybe:', taskTitle);
  
  // Demonstrate API client
  const apiClient = new HttpClient('https://api.example.com', {
    'Authorization': 'Bearer token123'
  });
  
  // This would make an actual HTTP request in a real application
  // const tasksResponse = await apiClient.get<Task[]>('/api/v1/tasks');
  // console.log('API Response:', tasksResponse);
}

// Run the demonstration
demonstrateTaskManagement().catch(console.error);

// Export types and classes for external use
export {
  Task,
  User,
  Project,
  TaskStatus,
  Priority,
  TaskService,
  TaskRepository,
  HttpClient,
  Maybe,
  Result,
  ServiceError,
  type ApiResponse,
  type Repository,
  type Service
}; 