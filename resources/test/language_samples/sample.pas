program SamplePascalProgram;

{$mode objfpc}{$H+}
{$APPTYPE CONSOLE}

{ Sample Pascal/Delphi/Object Pascal program demonstrating various language features }

uses
  SysUtils, Classes, Math, Variants, DateUtils;

type
  { Forward declarations }
  TAnimal = class;
  
  { Custom exception class }
  EInvalidAgeException = class(Exception);
  
  { Abstract base class demonstrating OOP concepts }
  TAnimal = class abstract
  private
    FName: string;
    FAge: Integer;
    FSpecies: string;
  protected
    procedure SetAge(const Value: Integer); virtual;
  public
    constructor Create(const AName, ASpecies: string; AAge: Integer);
    destructor Destroy; override;
    
    { Abstract method - must be implemented in derived classes }
    function MakeSound: string; virtual; abstract;
    
    { Virtual method with default implementation }
    function GetDescription: string; virtual;
    
    { Properties }
    property Name: string read FName write FName;
    property Age: Integer read FAge write SetAge;
    property Species: string read FSpecies;
  end;
  
  { Concrete implementation }
  TDog = class(TAnimal)
  public
    constructor Create(const AName: string; AAge: Integer);
    function MakeSound: string; override;
    function GetDescription: string; override;
    
    { Additional methods }
    procedure Fetch(const Item: string);
  end;
  
  { Another concrete implementation }
  TCat = class(TAnimal)
  private
    FIsIndoor: Boolean;
  public
    constructor Create(const AName: string; AAge: Integer; AIsIndoor: Boolean);
    function MakeSound: string; override;
    procedure Purr;
    
    property IsIndoor: Boolean read FIsIndoor write FIsIndoor;
  end;
  
  { Generic list demonstration }
  {$IFDEF FPC}
  generic TAnimalList<T: TAnimal> = class(TList)
  private
    function GetItem(Index: Integer): T;
    procedure SetItem(Index: Integer; const Value: T);
  public
    property Items[Index: Integer]: T read GetItem write SetItem; default;
    procedure AddAnimal(Animal: T);
  end;
  {$ENDIF}
  
  { Record type with methods (modern Pascal feature) }
  TPoint = record
    X, Y: Double;
    
    class function Create(AX, AY: Double): TPoint; static;
    function Distance(const Other: TPoint): Double;
    function ToString: string;
  end;
  
  { Enumeration with explicit values }
  TColor = (clRed = 1, clGreen = 2, clBlue = 4, clYellow = 8);
  TColors = set of TColor;
  
  { Variant record (union) }
  TShape = record
    case ShapeType: (stCircle, stRectangle, stTriangle) of
      stCircle: (Radius: Double);
      stRectangle: (Width, Height: Double);
      stTriangle: (Base, TriangleHeight: Double);
  end;

{ Global variables }
var
  GlobalCounter: Integer = 0;

{ Function with multiple parameters and default values }
function CalculateArea(const Shape: TShape; Precision: Integer = 2): Double;
begin
  case Shape.ShapeType of
    stCircle:
      Result := Pi * Sqr(Shape.Radius);
    stRectangle:
      Result := Shape.Width * Shape.Height;
    stTriangle:
      Result := 0.5 * Shape.Base * Shape.TriangleHeight;
  else
    Result := 0.0;
  end;
  
  Result := RoundTo(Result, -Precision);
end;

{ Procedure with var and const parameters }
procedure ProcessNumbers(const Input: array of Integer; var Sum, Average: Double; out Count: Integer);
var
  I: Integer;
begin
  Sum := 0;
  Count := Length(Input);
  
  for I := Low(Input) to High(Input) do
    Sum := Sum + Input[I];
    
  if Count > 0 then
    Average := Sum / Count
  else
    Average := 0;
end;

{ String manipulation example }
function FormatPersonInfo(const FirstName, LastName: string; Age: Integer): string;
begin
  Result := Format('%s, %s (Age: %d)', [LastName, FirstName, Age]);
end;

{ File I/O example }
procedure WriteToFile(const FileName, Content: string);
var
  FileStream: TFileStream;
  StringStream: TStringStream;
begin
  try
    FileStream := TFileStream.Create(FileName, fmCreate);
    try
      StringStream := TStringStream.Create(Content);
      try
        FileStream.CopyFrom(StringStream, 0);
      finally
        StringStream.Free;
      end;
    finally
      FileStream.Free;
    end;
  except
    on E: Exception do
      WriteLn('Error writing to file: ', E.Message);
  end;
end;

{ Exception handling example }
function SafeDivision(A, B: Double): Double;
begin
  try
    if B = 0 then
      raise EDivByZero.Create('Division by zero is not allowed');
    Result := A / B;
  except
    on E: EDivByZero do
    begin
      WriteLn('Division error: ', E.Message);
      Result := 0;
    end;
    on E: Exception do
    begin
      WriteLn('Unexpected error: ', E.Message);
      Result := 0;
    end;
  end;
end;

{ Implementation of TAnimal methods }
constructor TAnimal.Create(const AName, ASpecies: string; AAge: Integer);
begin
  inherited Create;
  FName := AName;
  FSpecies := ASpecies;
  SetAge(AAge);
end;

destructor TAnimal.Destroy;
begin
  WriteLn(Format('Animal %s has been destroyed', [FName]));
  inherited Destroy;
end;

procedure TAnimal.SetAge(const Value: Integer);
begin
  if Value < 0 then
    raise EInvalidAgeException.Create('Age cannot be negative');
  FAge := Value;
end;

function TAnimal.GetDescription: string;
begin
  Result := Format('%s is a %d-year-old %s', [FName, FAge, FSpecies]);
end;

{ Implementation of TDog methods }
constructor TDog.Create(const AName: string; AAge: Integer);
begin
  inherited Create(AName, 'Dog', AAge);
end;

function TDog.MakeSound: string;
begin
  Result := 'Woof! Woof!';
end;

function TDog.GetDescription: string;
begin
  Result := inherited GetDescription + ' and loves to play fetch!';
end;

procedure TDog.Fetch(const Item: string);
begin
  WriteLn(Format('%s is fetching the %s!', [Name, Item]));
end;

{ Implementation of TCat methods }
constructor TCat.Create(const AName: string; AAge: Integer; AIsIndoor: Boolean);
begin
  inherited Create(AName, 'Cat', AAge);
  FIsIndoor := AIsIndoor;
end;

function TCat.MakeSound: string;
begin
  Result := 'Meow! Purr...';
end;

procedure TCat.Purr;
begin
  WriteLn(Format('%s is purring contentedly...', [Name]));
end;

{ Implementation of TPoint methods }
class function TPoint.Create(AX, AY: Double): TPoint;
begin
  Result.X := AX;
  Result.Y := AY;
end;

function TPoint.Distance(const Other: TPoint): Double;
begin
  Result := Sqrt(Sqr(X - Other.X) + Sqr(Y - Other.Y));
end;

function TPoint.ToString: string;
begin
  Result := Format('(%.2f, %.2f)', [X, Y]);
end;

{ Main program }
var
  Dog: TDog;
  Cat: TCat;
  Numbers: array[1..5] of Integer = (10, 20, 30, 40, 50);
  Sum, Average: Double;
  Count: Integer;
  Point1, Point2: TPoint;
  Shape: TShape;
  Area: Double;
  Colors: TColors;
  I: Integer;

begin
  try
    WriteLn('=== Pascal/Delphi Sample Program ===');
    WriteLn;
    
    { Object-oriented programming example }
    WriteLn('--- Object-Oriented Programming ---');
    Dog := TDog.Create('Buddy', 3);
    Cat := TCat.Create('Whiskers', 2, True);
    
    try
      WriteLn(Dog.GetDescription);
      WriteLn('Dog says: ', Dog.MakeSound);
      Dog.Fetch('ball');
      WriteLn;
      
      WriteLn(Cat.GetDescription);
      WriteLn('Cat says: ', Cat.MakeSound);
      Cat.Purr;
      WriteLn;
    finally
      Dog.Free;
      Cat.Free;
    end;
    
    { Array processing }
    WriteLn('--- Array Processing ---');
    ProcessNumbers(Numbers, Sum, Average, Count);
    WriteLn(Format('Numbers processed: %d, Sum: %.2f, Average: %.2f', [Count, Sum, Average]));
    WriteLn;
    
    { Record and geometry calculations }
    WriteLn('--- Geometry Calculations ---');
    Point1 := TPoint.Create(0, 0);
    Point2 := TPoint.Create(3, 4);
    WriteLn(Format('Distance between %s and %s: %.2f', 
                   [Point1.ToString, Point2.ToString, Point1.Distance(Point2)]));
    
    { Variant record example }
    Shape.ShapeType := stCircle;
    Shape.Radius := 5.0;
    Area := CalculateArea(Shape);
    WriteLn(Format('Circle area (radius %.1f): %.2f', [Shape.Radius, Area]));
    
    Shape.ShapeType := stRectangle;
    Shape.Width := 4.0;
    Shape.Height := 6.0;
    Area := CalculateArea(Shape);
    WriteLn(Format('Rectangle area (%.1f x %.1f): %.2f', [Shape.Width, Shape.Height, Area]));
    WriteLn;
    
    { Set operations }
    WriteLn('--- Set Operations ---');
    Colors := [clRed, clBlue];
    if clRed in Colors then
      WriteLn('Red is in the color set');
    Colors := Colors + [clGreen];
    WriteLn(Format('Color set now contains %d colors', [Ord(clRed in Colors) + 
                    Ord(clGreen in Colors) + Ord(clBlue in Colors) + Ord(clYellow in Colors)]));
    WriteLn;
    
    { Exception handling }
    WriteLn('--- Exception Handling ---');
    WriteLn(Format('Safe division 10/2 = %.2f', [SafeDivision(10, 2)]));
    WriteLn(Format('Safe division 10/0 = %.2f', [SafeDivision(10, 0)]));
    WriteLn;
    
    { Loop examples }
    WriteLn('--- Loop Examples ---');
    Write('For loop: ');
    for I := 1 to 5 do
      Write(I, ' ');
    WriteLn;
    
    Write('While loop countdown: ');
    I := 5;
    while I > 0 do
    begin
      Write(I, ' ');
      Dec(I);
    end;
    WriteLn;
    
    { String operations }
    WriteLn('--- String Operations ---');
    WriteLn(FormatPersonInfo('John', 'Doe', 30));
    WriteLn(FormatPersonInfo('Jane', 'Smith', 25));
    
    WriteLn;
    WriteLn('Program completed successfully!');
    
  except
    on E: Exception do
    begin
      WriteLn('An error occurred: ', E.Message);
      ExitCode := 1;
    end;
  end;
  
  {$IFDEF MSWINDOWS}
  WriteLn('Press Enter to exit...');
  ReadLn;
  {$ENDIF}
end. 