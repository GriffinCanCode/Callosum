open Dsl_parser

let () =
  let content = {|personality "Creative Developer" {
  traits {
    creativity: 0.9;
    analytical: 0.7
  }
}|} in
  match Parser.parse_personality content with
  | Ok p -> Printf.printf "Parsed: %s with %d traits\n" p.name (List.length p.traits)
  | Error e -> Printf.printf "Error: %s\n" e
