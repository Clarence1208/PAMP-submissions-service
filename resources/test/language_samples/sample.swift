import Foundation
import UIKit
import SwiftUI
import Combine
import CoreData

// MARK: - Swift Sample Program
// This program demonstrates various Swift language features including:
// - Object-oriented programming with classes and structs
// - Protocol-oriented programming
// - Enums with associated values
// - Generics and type constraints
// - Error handling with Result types
// - Closures and higher-order functions
// - Property wrappers and SwiftUI
// - Combine framework usage
// - Memory management patterns

// MARK: - Error Types

enum NetworkError: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError(String)
    case serverError(Int)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL provided"
        case .noData:
            return "No data received from server"
        case .decodingError(let message):
            return "Decoding error: \(message)"
        case .serverError(let code):
            return "Server error with code: \(code)"
        }
    }
}

enum UserError: Error {
    case invalidAge
    case emptyName
    case duplicateEmail
}

// MARK: - Protocols

protocol Identifiable {
    var id: String { get }
}

protocol Drawable {
    func draw() -> String
}

protocol Serializable {
    func serialize() -> Data?
    static func deserialize(from data: Data) -> Self?
}

protocol NetworkService {
    associatedtype ResponseType: Codable
    func fetchData() async throws -> ResponseType
}

// MARK: - Enums

enum UserRole: String, CaseIterable, Codable {
    case admin = "admin"
    case moderator = "moderator"
    case user = "user"
    case guest = "guest"
    
    var permissions: [String] {
        switch self {
        case .admin:
            return ["read", "write", "delete", "manage"]
        case .moderator:
            return ["read", "write", "moderate"]
        case .user:
            return ["read", "write"]
        case .guest:
            return ["read"]
        }
    }
    
    var displayName: String {
        rawValue.capitalized
    }
}

enum APIEndpoint {
    case users
    case posts(userId: String)
    case comments(postId: String)
    case profile(userId: String)
    
    var path: String {
        switch self {
        case .users:
            return "/api/users"
        case .posts(let userId):
            return "/api/users/\(userId)/posts"
        case .comments(let postId):
            return "/api/posts/\(postId)/comments"
        case .profile(let userId):
            return "/api/users/\(userId)/profile"
        }
    }
}

enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)
    
    func map<NewSuccess>(_ transform: (Success) -> NewSuccess) -> Result<NewSuccess, Failure> {
        switch self {
        case .success(let value):
            return .success(transform(value))
        case .failure(let error):
            return .failure(error)
        }
    }
}

// MARK: - Models

struct User: Codable, Identifiable, Equatable, Hashable {
    let id: String
    var name: String
    var email: String
    var age: Int
    var role: UserRole
    var profileImage: URL?
    var createdAt: Date
    var isActive: Bool
    
    init(name: String, email: String, age: Int, role: UserRole = .user) throws {
        guard !name.isEmpty else { throw UserError.emptyName }
        guard age >= 13 else { throw UserError.invalidAge }
        
        self.id = UUID().uuidString
        self.name = name
        self.email = email
        self.age = age
        self.role = role
        self.profileImage = nil
        self.createdAt = Date()
        self.isActive = true
    }
    
    // Computed properties
    var isAdult: Bool {
        age >= 18
    }
    
    var displayName: String {
        "\(name) (\(role.displayName))"
    }
    
    // Mutating methods
    mutating func updateRole(_ newRole: UserRole) {
        role = newRole
    }
    
    mutating func deactivate() {
        isActive = false
    }
}

struct Post: Codable, Identifiable {
    let id: String
    let authorId: String
    var title: String
    var content: String
    var tags: [String]
    let createdAt: Date
    var updatedAt: Date
    var likesCount: Int
    var commentsCount: Int
    
    init(authorId: String, title: String, content: String, tags: [String] = []) {
        self.id = UUID().uuidString
        self.authorId = authorId
        self.title = title
        self.content = content
        self.tags = tags
        self.createdAt = Date()
        self.updatedAt = Date()
        self.likesCount = 0
        self.commentsCount = 0
    }
    
    mutating func addLike() {
        likesCount += 1
    }
    
    mutating func update(title: String? = nil, content: String? = nil, tags: [String]? = nil) {
        if let title = title { self.title = title }
        if let content = content { self.content = content }
        if let tags = tags { self.tags = tags }
        self.updatedAt = Date()
    }
}

// MARK: - Generic Types

class GenericContainer<T> {
    private var items: [T] = []
    
    var count: Int {
        items.count
    }
    
    var isEmpty: Bool {
        items.isEmpty
    }
    
    func add(_ item: T) {
        items.append(item)
    }
    
    func remove(at index: Int) -> T? {
        guard index < items.count else { return nil }
        return items.remove(at: index)
    }
    
    func get(at index: Int) -> T? {
        guard index < items.count else { return nil }
        return items[index]
    }
    
    func filter(_ predicate: (T) -> Bool) -> [T] {
        return items.filter(predicate)
    }
    
    func map<U>(_ transform: (T) -> U) -> [U] {
        return items.map(transform)
    }
}

struct Stack<Element> {
    private var items: [Element] = []
    
    var isEmpty: Bool {
        items.isEmpty
    }
    
    var count: Int {
        items.count
    }
    
    var top: Element? {
        items.last
    }
    
    mutating func push(_ item: Element) {
        items.append(item)
    }
    
    @discardableResult
    mutating func pop() -> Element? {
        return items.popLast()
    }
    
    func peek() -> Element? {
        return items.last
    }
}

// MARK: - Service Classes

class UserService: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let networkManager = NetworkManager()
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        loadSampleData()
    }
    
    private func loadSampleData() {
        do {
            let sampleUsers = [
                try User(name: "Alice Johnson", email: "alice@example.com", age: 28, role: .admin),
                try User(name: "Bob Smith", email: "bob@example.com", age: 34, role: .user),
                try User(name: "Carol Williams", email: "carol@example.com", age: 29, role: .moderator),
                try User(name: "David Brown", email: "david@example.com", age: 31, role: .user)
            ]
            self.users = sampleUsers
        } catch {
            print("Error creating sample users: \(error)")
        }
    }
    
    func fetchUsers() async {
        isLoading = true
        errorMessage = nil
        
        do {
            // Simulate network delay
            try await Task.sleep(nanoseconds: 1_000_000_000)
            
            // In a real app, you would fetch from a server
            await MainActor.run {
                self.isLoading = false
            }
        } catch {
            await MainActor.run {
                self.isLoading = false
                self.errorMessage = error.localizedDescription
            }
        }
    }
    
    func addUser(_ user: User) {
        users.append(user)
    }
    
    func removeUser(withId id: String) {
        users.removeAll { $0.id == id }
    }
    
    func updateUser(_ user: User) {
        if let index = users.firstIndex(where: { $0.id == user.id }) {
            users[index] = user
        }
    }
    
    // Higher-order functions examples
    func filterActiveUsers() -> [User] {
        users.filter { $0.isActive }
    }
    
    func usersByRole(_ role: UserRole) -> [User] {
        users.filter { $0.role == role }
    }
    
    func averageAge() -> Double {
        guard !users.isEmpty else { return 0 }
        let totalAge = users.map { $0.age }.reduce(0, +)
        return Double(totalAge) / Double(users.count)
    }
}

class NetworkManager {
    private let session = URLSession.shared
    private let baseURL = "https://api.example.com"
    
    func request<T: Codable>(
        endpoint: APIEndpoint,
        responseType: T.Type
    ) async throws -> T {
        guard let url = URL(string: baseURL + endpoint.path) else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.noData
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            throw NetworkError.serverError(httpResponse.statusCode)
        }
        
        do {
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decodingError(error.localizedDescription)
        }
    }
    
    // Generic method with constraints
    func fetchAndProcess<T: Codable & Identifiable>(
        endpoint: APIEndpoint,
        responseType: T.Type,
        processor: @escaping (T) -> T
    ) async throws -> T {
        let data = try await request(endpoint: endpoint, responseType: responseType)
        return processor(data)
    }
}

// MARK: - SwiftUI Views

struct ContentView: View {
    @StateObject private var userService = UserService()
    @State private var showingAddUser = false
    @State private var searchText = ""
    
    var filteredUsers: [User] {
        if searchText.isEmpty {
            return userService.users
        } else {
            return userService.users.filter { user in
                user.name.localizedCaseInsensitiveContains(searchText) ||
                user.email.localizedCaseInsensitiveContains(searchText)
            }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack {
                SearchBar(text: $searchText)
                
                if userService.isLoading {
                    ProgressView("Loading users...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(filteredUsers) { user in
                        UserRowView(user: user)
                            .swipeActions(edge: .trailing) {
                                Button("Delete", role: .destructive) {
                                    userService.removeUser(withId: user.id)
                                }
                            }
                    }
                }
                
                Spacer()
                
                if let errorMessage = userService.errorMessage {
                    Text("Error: \(errorMessage)")
                        .foregroundColor(.red)
                        .padding()
                }
            }
            .navigationTitle("Users")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Add User") {
                        showingAddUser = true
                    }
                }
            }
            .sheet(isPresented: $showingAddUser) {
                AddUserView(userService: userService)
            }
            .task {
                await userService.fetchUsers()
            }
        }
    }
}

struct UserRowView: View {
    let user: User
    
    var body: some View {
        HStack {
            AsyncImage(url: user.profileImage) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } placeholder: {
                Circle()
                    .fill(Color.gray.opacity(0.3))
            }
            .frame(width: 50, height: 50)
            .clipShape(Circle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(user.name)
                    .font(.headline)
                    .foregroundColor(user.isActive ? .primary : .secondary)
                
                Text(user.email)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                HStack {
                    Text("Age: \(user.age)")
                    Spacer()
                    Text(user.role.displayName)
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(roleColor(for: user.role))
                        .foregroundColor(.white)
                        .clipShape(Capsule())
                }
                .font(.caption)
            }
            
            Spacer()
            
            if !user.isActive {
                Image(systemName: "pause.circle.fill")
                    .foregroundColor(.orange)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func roleColor(for role: UserRole) -> Color {
        switch role {
        case .admin:
            return .red
        case .moderator:
            return .orange
        case .user:
            return .blue
        case .guest:
            return .gray
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search users...", text: $text)
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            if !text.isEmpty {
                Button("Clear") {
                    text = ""
                }
                .foregroundColor(.blue)
            }
        }
        .padding(.horizontal)
    }
}

struct AddUserView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var userService: UserService
    
    @State private var name = ""
    @State private var email = ""
    @State private var age = ""
    @State private var selectedRole = UserRole.user
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("User Information")) {
                    TextField("Name", text: $name)
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    TextField("Age", text: $age)
                        .keyboardType(.numberPad)
                }
                
                Section(header: Text("Role")) {
                    Picker("Role", selection: $selectedRole) {
                        ForEach(UserRole.allCases, id: \.self) { role in
                            Text(role.displayName).tag(role)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                Section {
                    Button("Add User") {
                        addUser()
                    }
                    .disabled(name.isEmpty || email.isEmpty || age.isEmpty)
                }
            }
            .navigationTitle("Add User")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert("Error", isPresented: $showingAlert) {
                Button("OK") { }
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func addUser() {
        guard let ageInt = Int(age) else {
            showAlert(message: "Please enter a valid age")
            return
        }
        
        do {
            let newUser = try User(name: name, email: email, age: ageInt, role: selectedRole)
            userService.addUser(newUser)
            dismiss()
        } catch {
            showAlert(message: error.localizedDescription)
        }
    }
    
    private func showAlert(message: String) {
        alertMessage = message
        showingAlert = true
    }
}

// MARK: - Property Wrappers

@propertyWrapper
struct Clamped<Value: Comparable> {
    private var value: Value
    private let range: ClosedRange<Value>
    
    init(wrappedValue: Value, _ range: ClosedRange<Value>) {
        self.range = range
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
    }
    
    var wrappedValue: Value {
        get { value }
        set { value = min(max(newValue, range.lowerBound), range.upperBound) }
    }
}

@propertyWrapper
struct UserDefault<T> {
    let key: String
    let defaultValue: T
    
    var wrappedValue: T {
        get {
            UserDefaults.standard.object(forKey: key) as? T ?? defaultValue
        }
        set {
            UserDefaults.standard.set(newValue, forKey: key)
        }
    }
}

// MARK: - Example Usage

class GameSettings: ObservableObject {
    @UserDefault(key: "player_name", defaultValue: "Player")
    var playerName: String
    
    @UserDefault(key: "difficulty_level", defaultValue: 1)
    var difficultyLevel: Int
    
    @UserDefault(key: "sound_enabled", defaultValue: true)
    var soundEnabled: Bool
    
    @Clamped(0...100)
    var volume: Int = 50
    
    @Clamped(1...10)
    var gameSpeed: Double = 5.0
}

// MARK: - Extensions

extension String {
    var isValidEmail: Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format:"SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: self)
    }
    
    func truncated(to length: Int) -> String {
        if self.count <= length {
            return self
        } else {
            return String(self.prefix(length)) + "..."
        }
    }
}

extension Array {
    func chunked(into size: Int) -> [[Element]] {
        return stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
    
    func grouped<Key: Hashable>(by keyPath: KeyPath<Element, Key>) -> [Key: [Element]] {
        return Dictionary(grouping: self) { $0[keyPath: keyPath] }
    }
}

extension Collection {
    var isNotEmpty: Bool {
        !isEmpty
    }
}

// MARK: - Async/Await Examples

actor DataCache {
    private var cache: [String: Any] = [:]
    
    func getValue(for key: String) -> Any? {
        cache[key]
    }
    
    func setValue(_ value: Any, for key: String) {
        cache[key] = value
    }
    
    func removeValue(for key: String) {
        cache.removeValue(forKey: key)
    }
    
    func clearAll() {
        cache.removeAll()
    }
}

class AsyncDataManager {
    private let cache = DataCache()
    private let networkManager = NetworkManager()
    
    func fetchUserData(userId: String) async throws -> User {
        // Check cache first
        if let cachedUser = await cache.getValue(for: "user_\(userId)") as? User {
            return cachedUser
        }
        
        // Fetch from network
        let user = try await networkManager.request(
            endpoint: .profile(userId: userId),
            responseType: User.self
        )
        
        // Cache the result
        await cache.setValue(user, for: "user_\(userId)")
        
        return user
    }
    
    func fetchMultipleUsers(userIds: [String]) async throws -> [User] {
        return try await withThrowingTaskGroup(of: User.self) { group in
            for userId in userIds {
                group.addTask {
                    try await self.fetchUserData(userId: userId)
                }
            }
            
            var users: [User] = []
            for try await user in group {
                users.append(user)
            }
            return users
        }
    }
}

// MARK: - Main Application

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil
    ) -> Bool {
        print("Swift Sample App Started!")
        
        // Example usage of various Swift features
        demonstrateSwiftFeatures()
        
        return true
    }
    
    private func demonstrateSwiftFeatures() {
        // Generic containers
        let userContainer = GenericContainer<User>()
        let numberStack = Stack<Int>()
        
        // Property wrappers
        let gameSettings = GameSettings()
        gameSettings.volume = 75
        gameSettings.gameSpeed = 8.5
        
        // Higher-order functions
        let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        let evenNumbers = numbers.filter { $0 % 2 == 0 }
        let squaredNumbers = numbers.map { $0 * $0 }
        let sum = numbers.reduce(0, +)
        
        print("Even numbers: \(evenNumbers)")
        print("Squared numbers: \(squaredNumbers)")
        print("Sum: \(sum)")
        
        // String extensions
        let email = "test@example.com"
        print("Is valid email: \(email.isValidEmail)")
        
        let longText = "This is a very long text that needs to be truncated"
        print("Truncated: \(longText.truncated(to: 20))")
        
        // Error handling with Result type
        let result = createUser(name: "John", email: "john@example.com", age: 25)
        switch result {
        case .success(let user):
            print("Created user: \(user.name)")
        case .failure(let error):
            print("Error creating user: \(error)")
        }
    }
    
    private func createUser(name: String, email: String, age: Int) -> Swift.Result<User, Error> {
        do {
            let user = try User(name: name, email: email, age: age)
            return .success(user)
        } catch {
            return .failure(error)
        }
    }
}

// MARK: - App Entry Point

@main
struct SwiftSampleApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
} 