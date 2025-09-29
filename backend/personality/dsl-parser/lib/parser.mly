%{
  open Types

  let create_location start_pos end_pos = {
    filename = start_pos.Lexing.pos_fname;
    start_line = start_pos.Lexing.pos_lnum;
    start_col = start_pos.Lexing.pos_cnum - start_pos.Lexing.pos_bol;
    end_line = end_pos.Lexing.pos_lnum;
    end_col = end_pos.Lexing.pos_cnum - end_pos.Lexing.pos_bol;
  }

  let parse_error_with_location start_pos end_pos message =
    let location = create_location start_pos end_pos in
    { message; location }
%}

(* Token definitions *)
%token <string> IDENT STRING
%token <float> FLOAT
%token <char> CHAR
%token PERSONALITY TRAITS KNOWLEDGE BEHAVIORS EVOLUTION DOMAIN
%token WHEN UNLESS WITH DECAY AMPLIFIES CONNECTS_TO EVOLVES_TO TRANSFORMS_TO
%token IF THEN PREFER SEEK AVOID LEARNS UNLOCK_DOMAIN ADD_CONNECTION TRAIT_KW
%token BEGINNER INTERMEDIATE ADVANCED EXPERT
%token TIME_DAY TIME_WEEK TIME_MONTH TIME_YEAR
%token LBRACE RBRACE LPAREN RPAREN LBRACKET RBRACKET
%token COLON SEMICOLON COMMA EQUALS PLUS PLUS_EQUALS MINUS MINUS_EQUALS
%token MULTIPLY DIVIDE GT LT ARROW BIDIRECTIONAL
%token EOF

(* Precedence and associativity *)
%right ARROW BIDIRECTIONAL
%left PLUS MINUS
%left MULTIPLY DIVIDE
%left GT LT

(* Start symbol *)
%start <Types.personality> personality

(* Type declarations for non-terminals *)
%type <Types.trait_spec list> traits_section trait_list
%type <Types.trait_spec> trait_spec
%type <Types.trait_modifier list> modifier_list
%type <Types.trait_modifier> modifier
%type <Types.time_unit> time_unit
%type <Types.context> context_expr
%type <Types.knowledge_domain list> knowledge_section domain_list
%type <Types.knowledge_domain> knowledge_domain  
%type <(string * Types.knowledge_level) list> topic_list
%type <string * Types.knowledge_level> topic
%type <Types.knowledge_level> knowledge_level
%type <Types.knowledge_connection list> connection_list
%type <Types.knowledge_connection> connection
%type <Types.behavior_rule list> behaviors_section behavior_list
%type <Types.behavior_rule> behavior_rule
%type <Types.behavior_condition> behavior_condition
%type <Types.behavior_action> behavior_action
%type <Types.evolution_spec list> evolution_section evolution_list
%type <Types.evolution_spec> evolution_spec
%type <Types.evolution_trigger> evolution_trigger
%type <Types.evolution_effect> evolution_effect

%%

(* Main grammar rules *)

personality:
  | PERSONALITY name = STRING LBRACE 
    traits = traits_section?
    knowledge = knowledge_section?
    behaviors = behaviors_section?  
    evolution = evolution_section?
    RBRACE EOF { 
      { name; 
        traits = Option.value traits ~default:[];
        knowledge = Option.value knowledge ~default:[];
        behaviors = Option.value behaviors ~default:[];
        evolution = Option.value evolution ~default:[] }
    }
  | error { 
      let start_pos = $startpos in
      let end_pos = $endpos in
      let err = parse_error_with_location start_pos end_pos 
        "Expected personality definition" in
      failwith (show_parse_error err)
    }

traits_section:
  | TRAITS LBRACE traits = trait_list RBRACE { traits }

trait_list:
  | (* empty *) { [] }
  | t = trait_spec { [t] }
  | t = trait_spec SEMICOLON ts = trait_list { t :: ts }
  | error SEMICOLON ts = trait_list { 
      let start_pos = $startpos in
      Printf.eprintf "Warning: Invalid trait at line %d, skipping\n" start_pos.pos_lnum;
      ts
    }

trait_spec:
  | name = IDENT COLON strength = FLOAT { 
      { name; strength; modifiers = [] }
    }
  | name = IDENT COLON strength = FLOAT WITH modifiers = modifier_list {
      { name; strength; modifiers }
    }
  | error { 
      let start_pos = $startpos in
      let end_pos = $endpos in
      let err = parse_error_with_location start_pos end_pos 
        "Invalid trait specification" in
      failwith (show_parse_error err)
    }

modifier_list:
  | m = modifier { [m] }
  | m = modifier COMMA ms = modifier_list { m :: ms }

modifier:
  | DECAY LPAREN rate = FLOAT DIVIDE unit = time_unit RPAREN { 
      Types.Decay (rate, unit) 
    }
  | WHEN context = context_expr { Types.When context }
  | UNLESS context = context_expr { Types.Unless context }
  | AMPLIFIES LPAREN trait = STRING COMMA factor = FLOAT RPAREN { 
      Types.Amplifies (trait, factor) 
    }
  | TRANSFORMS_TO LPAREN trait = STRING COMMA factor = FLOAT COMMA count = FLOAT RPAREN { 
      Types.Transforms_to (trait, factor, Int.of_float count)
    }

time_unit:
  | TIME_DAY { Types.Day }
  | TIME_WEEK { Types.Week }  
  | TIME_MONTH { Types.Month }
  | TIME_YEAR { Types.Year }

context_expr:
  | LPAREN ctx = STRING RPAREN { Types.Topic ctx }

knowledge_section:
  | KNOWLEDGE LBRACE domains = domain_list RBRACE { domains }

domain_list:
  | (* empty *) { [] }
  | d = knowledge_domain { [d] }
  | d = knowledge_domain ds = domain_list { d :: ds }

knowledge_domain:
  | DOMAIN LPAREN name = STRING RPAREN LBRACE 
    topics = topic_list
    connections = connection_list
    RBRACE { 
      { name; topics; connections }
    }
  | DOMAIN LPAREN name = STRING RPAREN LBRACE 
    topics = topic_list
    RBRACE { 
      { name; topics; connections = [] }
    }

topic_list:
  | (* empty *) { [] }
  | t = topic { [t] }
  | t = topic SEMICOLON ts = topic_list { t :: ts }

topic:
  | name = IDENT COLON level = knowledge_level { (name, level) }

knowledge_level:
  | BEGINNER { Types.Beginner }
  | INTERMEDIATE { Types.Intermediate }
  | ADVANCED { Types.Advanced }  
  | EXPERT { Types.Expert }

connection_list:
  | (* empty *) { [] }
  | c = connection { [c] }
  | c = connection SEMICOLON cs = connection_list { c :: cs }

connection:
  | from_domain = STRING CONNECTS_TO to_domain = STRING 
    WITH strength = FLOAT { 
      { from_domain; to_domain; strength; evolution_rate = None }
    }
  | from_domain = STRING EVOLVES_TO to_domain = STRING 
    WITH strength = FLOAT COMMA rate = FLOAT { 
      { from_domain; to_domain; strength; evolution_rate = Some rate }
    }

behaviors_section:
  | BEHAVIORS LBRACE behaviors = behavior_list RBRACE { behaviors }

behavior_list:
  | (* empty *) { [] }
  | b = behavior_rule { [b] }
  | b = behavior_rule SEMICOLON bs = behavior_list { b :: bs }

behavior_rule:
  | WHEN condition = behavior_condition ARROW action = behavior_action {
      { condition; action }
    }

behavior_condition:
  | cond = IDENT LPAREN RPAREN { 
      match cond with
      | "tired" -> Types.Tired
      | "motivated" -> Types.Motivated  
      | _ -> Types.Context_match cond
    }
  | trait = IDENT GT value = FLOAT { Types.Trait_above (trait, value) }
  | ctx = STRING { Types.Context_match ctx }

behavior_action:
  | PREFER LPAREN value = STRING RPAREN { Types.Prefer value }
  | SEEK LPAREN value = STRING RPAREN { Types.Seek value }
  | AVOID LPAREN value = STRING RPAREN { Types.Avoid value }
  | style = IDENT COLON value = STRING { Types.Set_style (style, value) }

evolution_section:
  | EVOLUTION LBRACE evolutions = evolution_list RBRACE { evolutions }

evolution_list:
  | (* empty *) { [] }
  | e = evolution_spec { [e] }
  | e = evolution_spec SEMICOLON es = evolution_list { e :: es }

evolution_spec:
  | IF trigger = evolution_trigger THEN action = evolution_effect {
      { trigger; action }
    }

evolution_trigger:
  | LEARNS LPAREN value = STRING RPAREN { Types.Learns value }
  | count = IDENT LPAREN value = FLOAT RPAREN { 
      match count with
      | "interactions" -> Types.Interaction_count (Int.of_float value)
      | _ -> Types.Feedback_score value
    }

evolution_effect:
  | TRAIT_KW LPAREN trait = STRING RPAREN PLUS_EQUALS adj = FLOAT { 
      Types.Trait_adjust (trait, adj) 
    }
  | TRAIT_KW LPAREN trait = STRING RPAREN MINUS_EQUALS adj = FLOAT { 
      Types.Trait_adjust (trait, -.adj) 
    }
  | UNLOCK_DOMAIN LPAREN domain = STRING RPAREN { 
      Types.Unlock_domain domain 
    }
  | ADD_CONNECTION LPAREN from_d = STRING COMMA to_d = STRING COMMA str = FLOAT RPAREN { 
      Types.Add_connection (from_d, to_d, str) 
    }