(** Abstract Syntax Tree for Personality DSL *)

include Types

(** Utility functions for AST manipulation *)

let create_personality name = {
  name;
  traits = [];
  knowledge = [];
  behaviors = [];
  evolution = [];
}

let add_trait (personality : personality) (trait : trait_spec) : personality = {
  personality with traits = trait :: personality.traits
}

let add_knowledge_domain personality domain = {
  personality with knowledge = domain :: personality.knowledge  
}

let add_behavior personality behavior = {
  personality with behaviors = behavior :: personality.behaviors
}

let add_evolution personality evolution = {
  personality with evolution = evolution :: personality.evolution
}

(** Parse a personality from string with comprehensive error handling *)
let parse_personality_from_string ?(filename="<string>") input =
  let lexbuf = Lexing.from_string input in
  Lexing.set_filename lexbuf filename;
  try
    let personality = Parser.personality Lexer.token lexbuf in
    Ok personality
  with
  | Lexer.Lexer_error error -> Error [error]
  | Parser.Error -> 
    let pos = Lexing.lexeme_start_p lexbuf in
    let location = { 
      filename;
      start_line = pos.pos_lnum;
      start_col = pos.pos_cnum - pos.pos_bol;
      end_line = pos.pos_lnum;
      end_col = pos.pos_cnum - pos.pos_bol + (String.length (Lexing.lexeme lexbuf));
    } in
    let error = { 
      message = "Parse error near: " ^ (Lexing.lexeme lexbuf);
      location 
    } in
    Error [error]
  | Failure msg ->
    let location = { 
      filename;
      start_line = 1; 
      start_col = 1; 
      end_line = 1; 
      end_col = 1 
    } in
    let error = { 
      message = "Parse failure: " ^ msg;
      location 
    } in
    Error [error]

(** Parse a personality from file *)  
let parse_personality_from_file filename =
  try
    let ic = open_in filename in
    let input = really_input_string ic (in_channel_length ic) in
    close_in ic;
    parse_personality_from_string ~filename input
  with
  | Sys_error msg -> 
    let location = { 
      filename;
      start_line = 1; 
      start_col = 1; 
      end_line = 1; 
      end_col = 1 
    } in
    let error = { 
      message = "File error: " ^ msg;
      location 
    } in
    Error [error]
