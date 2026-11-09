program Demo;
uses crt;
var
  a: array[1..10] of integer;
  i, n, s: integer;

{ Сумма элементов }
function Sum(n: integer): integer;
var k, t: integer;
begin
  t := 0;
  for k := 1 to n do
    t := t + a[k];
  Sum := t;
end;

begin
  readln(n);
  i := 1;
  while i <= n do
  begin
    read(a[i]);
    inc(i);
  end;
  repeat
    dec(n);
  until n = 0;
  case s of
    1, 2: writeln('a');
    3: begin s := 0; writeln('b') end;
  else
    writeln('c');
  end;
  if s > 0 then writeln(Sum(5)) else writeln('neg');
end.
