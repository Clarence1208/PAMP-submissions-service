% Sample MATLAB program
% Demonstrates various MATLAB features and syntax

function main()
    fprintf('MATLAB Programming Example\n');
    
    % Define sample data
    people = create_people_data();
    
    % Display people information
    display_people(people);
    
    % Perform array operations
    array_operations_demo();
    
    % Matrix operations
    matrix_operations_demo();
    
    % Plotting example
    plotting_demo();
    
    % Signal processing example
    signal_processing_demo();
    
    % Statistics example
    statistics_demo();
end

function people = create_people_data()
    % Create structure array for people
    people(1).name = 'Alice';
    people(1).age = 30;
    people(1).email = 'alice@example.com';
    people(1).active = true;
    
    people(2).name = 'Bob';
    people(2).age = 25;
    people(2).email = 'bob@example.com';
    people(2).active = false;
    
    people(3).name = 'Charlie';
    people(3).age = 35;
    people(3).email = 'charlie@example.com';
    people(3).active = true;
    
    people(4).name = 'Diana';
    people(4).age = 28;
    people(4).email = 'diana@example.com';
    people(4).active = true;
end

function display_people(people)
    fprintf('\nPeople Information:\n');
    fprintf('%-10s %-5s %-20s %-6s\n', 'Name', 'Age', 'Email', 'Active');
    fprintf('%s\n', repmat('-', 1, 50));
    
    for i = 1:length(people)
        person = people(i);
        active_str = '';
        if person.active
            active_str = 'Yes';
        else
            active_str = 'No';
        end
        
        fprintf('%-10s %-5d %-20s %-6s\n', ...
            person.name, person.age, person.email, active_str);
    end
    
    % Find adults
    ages = [people.age];
    adults = people(ages >= 25);
    fprintf('\nAdults (age >= 25): %d out of %d\n', length(adults), length(people));
    
    % Average age
    avg_age = mean(ages);
    fprintf('Average age: %.1f years\n', avg_age);
end

function array_operations_demo()
    fprintf('\nArray Operations Demo:\n');
    
    % Create arrays
    numbers = 1:10;
    squares = numbers.^2;
    even_numbers = numbers(mod(numbers, 2) == 0);
    
    fprintf('Numbers: ');
    fprintf('%d ', numbers);
    fprintf('\n');
    
    fprintf('Squares: ');
    fprintf('%d ', squares);
    fprintf('\n');
    
    fprintf('Even numbers: ');
    fprintf('%d ', even_numbers);
    fprintf('\n');
    
    % Array statistics
    fprintf('Sum: %d\n', sum(numbers));
    fprintf('Mean: %.1f\n', mean(numbers));
    fprintf('Standard deviation: %.2f\n', std(numbers));
    fprintf('Min: %d, Max: %d\n', min(numbers), max(numbers));
end

function matrix_operations_demo()
    fprintf('\nMatrix Operations Demo:\n');
    
    % Create matrices
    A = [1 2 3; 4 5 6; 7 8 9];
    B = magic(3);  % Magic square
    
    fprintf('Matrix A:\n');
    disp(A);
    
    fprintf('Matrix B (magic square):\n');
    disp(B);
    
    % Matrix operations
    C = A * B;
    fprintf('A * B:\n');
    disp(C);
    
    % Element-wise operations
    D = A .* B;
    fprintf('A .* B (element-wise multiplication):\n');
    disp(D);
    
    % Matrix properties
    fprintf('Determinant of A: %.2f\n', det(A));
    fprintf('Rank of A: %d\n', rank(A));
    fprintf('Condition number of B: %.2f\n', cond(B));
    
    % Eigenvalues and eigenvectors
    [V, D_eigen] = eig(B);
    fprintf('Eigenvalues of B: ');
    fprintf('%.2f ', diag(D_eigen));
    fprintf('\n');
end

function plotting_demo()
    fprintf('\nPlotting Demo:\n');
    
    % Generate data
    x = linspace(0, 2*pi, 100);
    y1 = sin(x);
    y2 = cos(x);
    y3 = sin(2*x);
    
    % Create figure
    figure('Name', 'MATLAB Plotting Demo', 'NumberTitle', 'off');
    
    % Subplot 1: Basic plot
    subplot(2, 2, 1);
    plot(x, y1, 'b-', x, y2, 'r--', 'LineWidth', 2);
    title('Sine and Cosine Functions');
    xlabel('x (radians)');
    ylabel('y');
    legend('sin(x)', 'cos(x)', 'Location', 'best');
    grid on;
    
    % Subplot 2: Scatter plot
    subplot(2, 2, 2);
    scatter(y1, y2, 50, x, 'filled');
    title('Parametric Plot: cos(x) vs sin(x)');
    xlabel('sin(x)');
    ylabel('cos(x)');
    colorbar;
    axis equal;
    
    % Subplot 3: Bar plot
    subplot(2, 2, 3);
    data = [3 7 2 9 5 8];
    categories = {'A', 'B', 'C', 'D', 'E', 'F'};
    bar(data, 'FaceColor', [0.5 0.8 0.9]);
    title('Sample Bar Chart');
    xlabel('Categories');
    ylabel('Values');
    set(gca, 'XTickLabel', categories);
    
    % Subplot 4: 3D surface
    subplot(2, 2, 4);
    [X, Y] = meshgrid(-2:0.1:2, -2:0.1:2);
    Z = X.^2 + Y.^2;
    surf(X, Y, Z);
    title('3D Surface Plot: z = x² + y²');
    xlabel('x');
    ylabel('y');
    zlabel('z');
    shading interp;
    
    fprintf('Plotting completed. Check figure window.\n');
end

function signal_processing_demo()
    fprintf('\nSignal Processing Demo:\n');
    
    % Generate sample signal
    fs = 1000;  % Sampling frequency
    t = 0:1/fs:1;  % Time vector
    
    % Composite signal
    f1 = 50;   % Frequency 1
    f2 = 120;  % Frequency 2
    signal = sin(2*pi*f1*t) + 0.5*sin(2*pi*f2*t) + 0.2*randn(size(t));
    
    % Compute FFT
    Y = fft(signal);
    f = (0:length(Y)-1)*fs/length(Y);
    
    % Find peaks
    [peaks, locations] = findpeaks(abs(Y(1:length(Y)/2)), ...
        'MinPeakHeight', max(abs(Y))*0.1);
    
    fprintf('Signal contains frequencies at: ');
    for i = 1:length(locations)
        fprintf('%.1f Hz ', f(locations(i)));
    end
    fprintf('\n');
    
    % Filter the signal
    [b, a] = butter(4, [40 80]/(fs/2), 'bandpass');
    filtered_signal = filter(b, a, signal);
    
    fprintf('Applied bandpass filter (40-80 Hz)\n');
    fprintf('Original signal energy: %.2f\n', sum(signal.^2));
    fprintf('Filtered signal energy: %.2f\n', sum(filtered_signal.^2));
end

function statistics_demo()
    fprintf('\nStatistics Demo:\n');
    
    % Generate random data
    rng(42);  % Set seed for reproducibility
    data1 = normrnd(10, 2, 100, 1);  % Normal distribution
    data2 = unifrnd(5, 15, 100, 1);  % Uniform distribution
    
    % Descriptive statistics
    fprintf('Dataset 1 (Normal distribution):\n');
    fprintf('  Mean: %.2f, Std: %.2f\n', mean(data1), std(data1));
    fprintf('  Median: %.2f, IQR: %.2f\n', median(data1), iqr(data1));
    fprintf('  Min: %.2f, Max: %.2f\n', min(data1), max(data1));
    
    fprintf('Dataset 2 (Uniform distribution):\n');
    fprintf('  Mean: %.2f, Std: %.2f\n', mean(data2), std(data2));
    fprintf('  Median: %.2f, IQR: %.2f\n', median(data2), iqr(data2));
    fprintf('  Min: %.2f, Max: %.2f\n', min(data2), max(data2));
    
    % Correlation
    correlation = corrcoef(data1, data2);
    fprintf('Correlation between datasets: %.3f\n', correlation(1,2));
    
    % Statistical tests
    [h, p] = ttest2(data1, data2);
    fprintf('T-test (different means): h=%d, p=%.4f\n', h, p);
    
    % Linear regression
    X = [ones(length(data1), 1), data1];
    beta = X \ data2;
    fprintf('Linear regression: y = %.2fx + %.2f\n', beta(2), beta(1));
    
    % R-squared
    y_pred = X * beta;
    ss_res = sum((data2 - y_pred).^2);
    ss_tot = sum((data2 - mean(data2)).^2);
    r_squared = 1 - ss_res/ss_tot;
    fprintf('R-squared: %.3f\n', r_squared);
end

% Utility function for greeting
function greeting = greet_person(name, age)
    greeting = sprintf('Hello, %s! You are %d years old.', name, age);
end

% Custom function for factorial calculation
function result = factorial_custom(n)
    if n <= 1
        result = 1;
    else
        result = n * factorial_custom(n - 1);
    end
end

% Run main function if this file is executed directly
if ~exist('calling_function', 'var')
    main();
end 