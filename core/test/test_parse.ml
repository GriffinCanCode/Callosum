open Dsl_parser

let () =
  let content = {|personality "Creative Developer" {
  traits {
    creativity: 0.9;
    analytical: 0.7
  }
}|} in
  match Ast.parse_personality_from_string content with
  | Ok p -> Printf.printf "Parsed: %s with %d traits\n" p.Types.name (List.length p.Types.traits)
  | Error errors -> Printf.printf "Parse errors: %d\n" (List.length errors)
