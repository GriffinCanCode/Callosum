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

(* Character classes - more flexible whitespace *)
let whitespace = [' ' '\t']
let newline = '\r' | '\n' | "\r\n"
let any_whitespace = whitespace | newline
let digit = ['0'-'9']  
let alpha = ['a'-'z' 'A'-'Z']
let ident_char = alpha | digit | '_'
let ident = alpha ident_char*
let float_num = digit+ ('.' digit+)?
let string_char = [^ '"' '\n' '\r']

rule token = parse
  (* Whitespace and comments - more flexible *)
  | whitespace+ { token lexbuf }
  | newline { next_line lexbuf; token lexbuf }
  | newline+ { 
      (* Handle multiple consecutive newlines *)
      String.iter (function
        | '\n' | '\r' -> next_line lexbuf
        | _ -> ()) (Lexing.lexeme lexbuf);
      token lexbuf 
    }
  | "#" [^ '\n' '\r']* { token lexbuf }
  
  (* Main keywords *)
  | "personality" { PERSONALITY }
  | "traits" { TRAITS }
  | "knowledge" { KNOWLEDGE }
  | "behaviors" { BEHAVIORS } 
  | "evolution" { EVOLUTION }
  | "domain" { DOMAIN }
  
  (* Trait modifiers - more natural syntax *)
  | "amplifies" { AMPLIFIES }
  | "decays" { DECAY }
  | "when" { WHEN }
  | "unless" { UNLESS }
  | "connects_to" { CONNECTS_TO }
  
  (* Behavior keywords *)
  | "prefer" { PREFER }
  | "seek" { SEEK }
  | "avoid" { AVOID }
  | "after" { AFTER }
  
  (* Evolution keywords *)
  | "learns" { LEARNS }
  | "unlock" { UNLOCK }
  | "connect" { CONNECT }
  | "interactions" { INTERACTIONS }
  
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
  
  (* Operators and punctuation - simplified *)
  | ":" { COLON }
  | ";" { SEMICOLON }  (* Optional statement terminator *)
  | "(" { LPAREN }
  | ")" { RPAREN }
  | "+=" { PLUS_EQUALS }
  | "-" whitespace+ { LIST_ITEM }  (* List item marker - flexible whitespace *)
  | "*" { MULTIPLY }
  | "/" { DIVIDE }
  | ">" { GT }
  | "→" | "->" { ARROW }
  | "↔" | "<->" { BIDIRECTIONAL }
  
  (* Literals *)
  | float_num as f { 
      try FLOAT (Float.of_string f) 
      with Failure _ -> error lexbuf ("Invalid float: " ^ f)
    }
  | ident as s { IDENT s }
  | '"' (string_char* as s) '"' { STRING s }
  
  (* End of file *)
  | eof { EOF }
  
  (* Error cases *)
  | '"' [^ '"' '\n']* eof { error lexbuf "Unterminated string literal" }
  | '"' [^ '"' '\n']* '\n' { error lexbuf "String literal contains newline" }
  | _ as c { error lexbuf ("Unexpected character: '" ^ String.make 1 c ^ "'") }