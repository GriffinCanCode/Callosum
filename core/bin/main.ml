open Base
open Stdio
open Dsl_parser

let usage_msg = "dsl-parser [--input <file>] [--output <format>] [--context <string>]"
let input_file = ref ""
let output_format = ref "json"
let context_hint = ref ""

let set_input filename = input_file := filename
let set_output format = output_format := format  
let set_context ctx = context_hint := ctx

let speclist =
  [("--input", Stdlib.Arg.String set_input, " Input .colo file");
   ("-i", Stdlib.Arg.String set_input, " Input .colo file (short)");
   ("--output", Stdlib.Arg.String set_output, " Output format (json|prompt|lua|sql|cypher)");
   ("-o", Stdlib.Arg.String set_output, " Output format (short)");
   ("--context", Stdlib.Arg.String set_context, " Context hint for prompt generation");
   ("-c", Stdlib.Arg.String set_context, " Context hint (short)");
   ("--version", Stdlib.Arg.Unit (fun () -> printf "dsl-parser v0.2.0\n"; Stdlib.exit 0), " Show version");
   ("-v", Stdlib.Arg.Unit (fun () -> printf "dsl-parser v0.2.0\n"; Stdlib.exit 0), " Show version (short)")]

let string_to_target = function
  | "json" -> Some Compiler.Json
  | "prompt" -> Some Compiler.Prompt  
  | "lua" -> Some Compiler.Lua
  | "sql" -> Some Compiler.Sql
  | "cypher" -> Some Compiler.Cypher
  | _ -> None

let read_file_or_stdin filename =
  if String.is_empty filename || String.equal filename "-" then
    In_channel.input_all In_channel.stdin
  else
    In_channel.read_all filename

let compile_and_output dsl_content target _context =
  match Ast.parse_personality_from_string ~filename:(!input_file) dsl_content with
  | Error errors ->
      eprintf "Parse errors:\n";
      List.iter errors ~f:(fun e -> 
        eprintf "  %s at line %d:%d\n" e.Types.message e.Types.location.start_line e.Types.location.start_col
      );
      Stdlib.exit 1
  | Ok personality ->
      let context_opt = if String.is_empty !context_hint then None else Some !context_hint in
      match Compiler.compile personality target ?context:context_opt () with
      | Error errors ->
          eprintf "Compilation errors:\n";
          List.iter errors ~f:(fun e -> 
            eprintf "  %s\n" (Compiler.compiler_error_to_string e)
          );
          Stdlib.exit 1
      | Ok output ->
          printf "%s" output;
          Stdlib.exit 0

let () =
  Stdlib.Arg.parse speclist (fun _ -> ()) usage_msg;
  
  (* Validate arguments *)
  let target = match string_to_target !output_format with
    | Some t -> t
    | None -> 
        eprintf "Invalid output format: %s\n" !output_format;
        eprintf "Valid formats: json, prompt, lua, sql, cypher\n";
        Stdlib.exit 1
  in
  
  (* Read input *)
  let dsl_content = 
    try read_file_or_stdin !input_file
    with Sys_error msg -> 
      eprintf "Error reading input: %s\n" msg;
      Stdlib.exit 1
  in
  
  if String.is_empty (String.strip dsl_content) then (
    eprintf "Error: No DSL content provided\n";
    eprintf "%s\n" usage_msg;
    Stdlib.exit 1
  );
  
  (* Compile and output *)
  compile_and_output dsl_content target !context_hint