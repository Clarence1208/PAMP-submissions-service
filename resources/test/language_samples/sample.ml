(* Sample OCaml program *)

(* Define a record type *)
type person = {
  name : string;
  age : int;
  email : string;
}

(* Define a variant type *)
type priority = 
  | Low
  | Medium 
  | High
  | Urgent

(* Define a task type *)
type task = {
  title : string;
  priority : priority;
  completed : bool;
}

(* Function to greet a person *)
let greet person =
  Printf.sprintf "Hello, %s! You are %d years old." person.name person.age

(* Function to check if person is adult *)
let is_adult person = person.age >= 18

(* Function to convert priority to string *)
let priority_to_string = function
  | Low -> "Low"
  | Medium -> "Medium"
  | High -> "High"
  | Urgent -> "Urgent"

(* Function to get priority level *)
let priority_level = function
  | Low -> 1
  | Medium -> 2
  | High -> 3
  | Urgent -> 4

(* Higher-order function: map *)
let rec map f = function
  | [] -> []
  | h :: t -> f h :: map f t

(* Higher-order function: filter *)
let rec filter predicate = function
  | [] -> []
  | h :: t -> 
    if predicate h then h :: filter predicate t
    else filter predicate t

(* Higher-order function: fold_left *)
let rec fold_left f acc = function
  | [] -> acc
  | h :: t -> fold_left f (f acc h) t

(* Function composition *)
let compose f g x = f (g x)

(* Curry and uncurry examples *)
let add x y = x + y
let add_curried = fun x -> fun y -> x + y
let uncurry f (x, y) = f x y

(* Fibonacci with memoization using hashtable *)
let fibonacci =
  let memo = Hashtbl.create 100 in
  let rec fib n =
    try Hashtbl.find memo n
    with Not_found ->
      let result = 
        if n <= 1 then n
        else fib (n - 1) + fib (n - 2)
      in
      Hashtbl.add memo n result;
      result
  in fib

(* List processing functions *)
let rec take n lst =
  if n <= 0 then []
  else match lst with
    | [] -> []
    | h :: t -> h :: take (n - 1) t

let rec drop n lst =
  if n <= 0 then lst
  else match lst with
    | [] -> []
    | _ :: t -> drop (n - 1) t

(* Function to find maximum using option type *)
let rec find_max = function
  | [] -> None
  | [x] -> Some x
  | h :: t -> 
    match find_max t with
    | None -> Some h
    | Some max_rest -> Some (max h max_rest)

(* Pattern matching example *)
let describe_list = function
  | [] -> "Empty list"
  | [x] -> Printf.sprintf "Single element: %d" x
  | [x; y] -> Printf.sprintf "Two elements: %d and %d" x y
  | h :: _ -> Printf.sprintf "List starting with %d" h

(* Function using partial application *)
let add_ten = add 10
let multiply_by x y = x * y
let double = multiply_by 2

(* Module example *)
module MathUtils = struct
  let square x = x * x
  let cube x = x * x * x
  let power base exp = 
    let rec power_aux acc = function
      | 0 -> acc
      | n -> power_aux (acc * base) (n - 1)
    in power_aux 1 exp
  
  let factorial n =
    let rec fact_aux acc = function
      | 0 | 1 -> acc
      | n -> fact_aux (acc * n) (n - 1)
    in fact_aux 1 n
end

(* Using option and result types *)
let safe_divide x y =
  if y = 0 then None
  else Some (x / y)

type ('a, 'b) result = Ok of 'a | Error of 'b

let safe_divide_result x y =
  if y = 0 then Error "Division by zero"
  else Ok (x / y)

(* Tail-recursive sum *)
let sum_list lst =
  let rec sum_aux acc = function
    | [] -> acc
    | h :: t -> sum_aux (acc + h) t
  in sum_aux 0 lst

(* Main function *)
let main () =
  Printf.printf "OCaml Programming Example\n\n";
  
  (* Create sample people *)
  let people = [
    { name = "Alice"; age = 30; email = "alice@example.com" };
    { name = "Bob"; age = 17; email = "bob@example.com" };
    { name = "Charlie"; age = 35; email = "charlie@example.com" };
    { name = "Diana"; age = 25; email = "diana@example.com" };
  ] in
  
  Printf.printf "All people:\n";
  List.iter (fun person -> Printf.printf "%s\n" (greet person)) people;
  
  (* Filter adults *)
  let adults = filter is_adult people in
  Printf.printf "\nAdults:\n";
  List.iter (fun person -> Printf.printf "- %s\n" person.name) adults;
  
  (* Map to names *)
  let names = map (fun person -> person.name) people in
  Printf.printf "\nNames: %s\n" (String.concat ", " names);
  
  (* Sum of ages *)
  let ages = map (fun person -> person.age) people in
  let total_age = sum_list ages in
  let avg_age = float_of_int total_age /. float_of_int (List.length ages) in
  Printf.printf "Total age: %d\n" total_age;
  Printf.printf "Average age: %.1f\n" avg_age;
  
  (* Number operations *)
  let numbers = [1; 2; 3; 4; 5; 6; 7; 8; 9; 10] in
  let squares = map MathUtils.square numbers in
  let even_numbers = filter (fun x -> x mod 2 = 0) numbers in
  
  Printf.printf "\nNumbers: [%s]\n" (String.concat "; " (map string_of_int numbers));
  Printf.printf "Squares: [%s]\n" (String.concat "; " (map string_of_int squares));
  Printf.printf "Even numbers: [%s]\n" (String.concat "; " (map string_of_int even_numbers));
  
  (* Fibonacci sequence *)
  Printf.printf "\nFibonacci sequence (first 10):\n";
  for i = 0 to 9 do
    Printf.printf "%d " (fibonacci i)
  done;
  Printf.printf "\n";
  
  (* Function composition example *)
  let add_then_double = compose double add_ten in
  Printf.printf "\nFunction composition (add 10 then double 5): %d\n" (add_then_double 5);
  
  (* Pattern matching on lists *)
  let test_lists = [
    [];
    [42];
    [1; 2];
    [1; 2; 3; 4; 5];
  ] in
  
  Printf.printf "\nList descriptions:\n";
  List.iter (fun lst -> 
    Printf.printf "%s\n" (describe_list lst)
  ) test_lists;
  
  (* Option type example *)
  (match find_max numbers with
   | None -> Printf.printf "No maximum found\n"
   | Some max_val -> Printf.printf "Maximum value: %d\n" max_val);
  
  (* Safe division examples *)
  Printf.printf "\nSafe division examples:\n";
  (match safe_divide 10 2 with
   | None -> Printf.printf "Division failed\n"
   | Some result -> Printf.printf "10 / 2 = %d\n" result);
  
  (match safe_divide 10 0 with
   | None -> Printf.printf "Cannot divide by zero\n"
   | Some result -> Printf.printf "10 / 0 = %d\n" result);
  
  (* Task management example *)
  let tasks = [
    { title = "Review code"; priority = High; completed = false };
    { title = "Write documentation"; priority = Medium; completed = true };
    { title = "Fix bug"; priority = Urgent; completed = false };
    { title = "Refactor module"; priority = Low; completed = false };
  ] in
  
  Printf.printf "\nTasks by priority:\n";
  let sorted_tasks = List.sort (fun t1 t2 -> 
    compare (priority_level t2.priority) (priority_level t1.priority)
  ) tasks in
  
  List.iter (fun task ->
    let status = if task.completed then "✓" else "○" in
    Printf.printf "%s %s [%s]\n" status task.title (priority_to_string task.priority)
  ) sorted_tasks;
  
  Printf.printf "\nProgram completed successfully!\n"

(* Run main function *)
let () = main () 