{
open Parser
open Types

exception Lexer_error of parse_error

let create_location filename start_pos end_pos = {
  filename;
  start_line = start_pos.Lexing.pos_lnum;
  start_col = start_pos.Lexing.pos_cnum - start_pos.Lexing.pos_bol;
  end_line = end_pos.Lexing.pos_lnum;
  end_col = end_pos.Lexing.pos_cnum - end_pos.Lexing.pos_bol;
}

let current_location lexbuf = 
  create_location 
    "<unknown>"
    (Lexing.lexeme_start_p lexbuf)
    (Lexing.lexeme_end_p lexbuf)

let error lexbuf message =
  let location = current_location lexbuf in
  raise (Lexer_error { message; location })

let next_line lexbuf =
  Lexing.new_line lexbuf
}

(* Character classes *)
let whitespace = [' ' '\t']
let newline = '\r' | '\n' | "\r\n"
let digit = ['0'-'9']  
let alpha = ['a'-'z' 'A'-'Z']
let ident_char = alpha | digit | '_'
let ident = alpha ident_char*
let float_num = digit+ ('.' digit+)?
let string_char = [^ '"' '\n' '\r']

rule token = parse
  (* Whitespace and comments *)
  | whitespace { token lexbuf }
  | newline { next_line lexbuf; token lexbuf }
  | "//" [^ '\n' '\r']* { token lexbuf }
  | "/*" { comment_block 1 lexbuf }
  
  (* Keywords *)
  | "personality" { PERSONALITY }
  | "traits" { TRAITS }
  | "knowledge" { KNOWLEDGE }
  | "behaviors" { BEHAVIORS } 
  | "evolution" { EVOLUTION }
  | "domain" { DOMAIN }
  | "when" { WHEN }
  | "unless" { UNLESS }
  | "with" { WITH }
  | "decay" { DECAY }
  | "amplifies" { AMPLIFIES }
  | "connects_to" { CONNECTS_TO }
  | "if" { IF }
  | "then" { THEN }
  | "evolves_to" { EVOLVES_TO }
  | "transforms_to" { TRANSFORMS_TO }
  | "prefer" { PREFER }
  | "seek" { SEEK }
  | "avoid" { AVOID }
  | "learns" { LEARNS }
  | "unlock_domain" { UNLOCK_DOMAIN }
  | "add_connection" { ADD_CONNECTION }
  | "trait" { TRAIT_KW }
  
  (* Knowledge levels *)
  | "beginner" { BEGINNER }
  | "intermediate" { INTERMEDIATE } 
  | "advanced" { ADVANCED }
  | "expert" { EXPERT }
  
  (* Time units *)
  | "day" | "days" { TIME_DAY }
  | "week" | "weeks" { TIME_WEEK }
  | "month" | "months" { TIME_MONTH }
  | "year" | "years" { TIME_YEAR }
  
  (* Operators and punctuation *)
  | "{" { LBRACE }
  | "}" { RBRACE }
  | "(" { LPAREN }
  | ")" { RPAREN }
  | "[" { LBRACKET }
  | "]" { RBRACKET }
  | ":" { COLON }
  | ";" { SEMICOLON }  
  | "," { COMMA }
  | "=" { EQUALS }
  | "+" { PLUS }
  | "+=" { PLUS_EQUALS }
  | "-" { MINUS }
  | "-=" { MINUS_EQUALS }
  | "*" { MULTIPLY }
  | "/" { DIVIDE }
  | ">" { GT }
  | "<" { LT }
  | "->" { ARROW }
  | "<->" { BIDIRECTIONAL }
  
  (* Literals *)
  | float_num as f { 
      try FLOAT (Float.of_string f) 
      with Failure _ -> error lexbuf ("Invalid float: " ^ f)
    }
  | ident as s { IDENT s }
  | '"' (string_char* as s) '"' { STRING s }
  | '\'' ([^ '\''] as c) '\'' { CHAR c }
  
  (* End of file *)
  | eof { EOF }
  
  (* Error cases *)
  | '"' [^ '"' '\n']* eof { error lexbuf "Unterminated string literal" }
  | '"' [^ '"' '\n']* '\n' { error lexbuf "String literal contains newline" }
  | _ as c { error lexbuf ("Unexpected character: '" ^ String.make 1 c ^ "'") }

and comment_block depth = parse
  | "/*" { comment_block (depth + 1) lexbuf }
  | "*/" { 
      if depth = 1 then token lexbuf 
      else comment_block (depth - 1) lexbuf 
    }
  | newline { next_line lexbuf; comment_block depth lexbuf }
  | eof { error lexbuf "Unterminated comment block" }
  | _ { comment_block depth lexbuf }