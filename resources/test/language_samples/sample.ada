-- Sample Ada program
with Ada.Text_IO; use Ada.Text_IO;

procedure Hello_World is
   type Person_Type is record
      Name : String(1..50);
      Age  : Natural;
   end record;
   
   procedure Greet(P : Person_Type) is
   begin
      Put_Line("Hello, " & P.Name & "! You are" & Natural'Image(P.Age) & " years old.");
   end Greet;
   
   My_Person : Person_Type := (Name => "Alice" & (6..50 => ' '), Age => 30);
begin
   Put_Line("Ada Programming Example");
   Greet(My_Person);
end Hello_World; 