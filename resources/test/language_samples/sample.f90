! Sample Fortran program
program sample_fortran
    implicit none
    
    ! Variable declarations
    integer, parameter :: n = 5
    integer :: i, factorial_result
    real, dimension(n) :: numbers
    real :: average
    
    ! Derived type
    type :: person_type
        character(len=50) :: name
        integer :: age
    end type person_type
    
    type(person_type) :: person
    
    ! Initialize person
    person%name = "Alice"
    person%age = 30
    
    write(*,*) 'Fortran Programming Example'
    write(*,*) 'Person: ', trim(person%name), ', Age: ', person%age
    
    ! Array operations
    do i = 1, n
        numbers(i) = real(i) * 2.5
    end do
    
    ! Calculate average
    average = sum(numbers) / real(n)
    write(*,*) 'Numbers: ', numbers
    write(*,*) 'Average: ', average
    
    ! Call subroutines and functions
    call greet_person(person)
    factorial_result = factorial(5)
    write(*,*) 'Factorial of 5: ', factorial_result
    
end program sample_fortran

! Subroutine
subroutine greet_person(p)
    implicit none
    type :: person_type
        character(len=50) :: name
        integer :: age
    end type person_type
    
    type(person_type), intent(in) :: p
    
    write(*,*) 'Hello, ', trim(p%name), '! You are ', p%age, ' years old.'
end subroutine greet_person

! Function
integer function factorial(n)
    implicit none
    integer, intent(in) :: n
    integer :: i
    
    factorial = 1
    do i = 1, n
        factorial = factorial * i
    end do
end function factorial 