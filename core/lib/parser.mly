%{
  open Types

  (* let create_location start_pos end_pos = {
    filename = start_pos.Lexing.pos_fname;
    start_line = start_pos.Lexing.pos_lnum;
    start_col = start_pos.Lexing.pos_cnum - start_pos.Lexing.pos_bol;
    end_line = end_pos.Lexing.pos_lnum;
    end_col = end_pos.Lexing.pos_cnum - end_pos.Lexing.pos_bol;
  } *)

  (* let parse_error_with_location start_pos end_pos message =
    let location = create_location start_pos end_pos in
    { message; location } *)
%}

(* Token definitions - clean and minimal *)
%token <string> IDENT STRING
%token <float> FLOAT
%token PERSONALITY TRAITS KNOWLEDGE BEHAVIORS EVOLUTION DOMAIN
%token WHEN UNLESS AMPLIFIES DECAY CONNECTS_TO
%token PREFER SEEK AVOID AFTER LEARNS UNLOCK CONNECT INTERACTIONS
%token BEGINNER INTERMEDIATE ADVANCED EXPERT
%token TIME_DAY TIME_WEEK TIME_MONTH TIME_YEAR
%token LPAREN RPAREN COLON SEMICOLON PLUS_EQUALS MULTIPLY DIVIDE
%token GT ARROW BIDIRECTIONAL LIST_ITEM
%token EOF

(* Start symbol *)
%start <Types.personality> personality

%%

(* Main grammar rules *)

personality:
  | PERSONALITY optional_colon name = STRING optional_semicolon
    sections = section_list
    EOF { 
      let traits = ref [] in
      let knowledge = ref [] in  
      let behaviors = ref [] in
      let evolution = ref [] in
      List.iter (function
        | `Traits t -> traits := t
        | `Knowledge k -> knowledge := k
        | `Behaviors b -> behaviors := b
        | `Evolution e -> evolution := e
      ) sections;
      { name; 
        traits = !traits;
        knowledge = !knowledge;
        behaviors = !behaviors;
        evolution = !evolution }
    }

section_list:
  | (* empty *) { [] }
  | s = section rest = section_list { s :: rest }

(* Helper rules for optional punctuation *)
optional_colon:
  | (* empty *) { () }
  | COLON { () }

optional_semicolon:
  | (* empty *) { () }
  | SEMICOLON { () }

section:
  | TRAITS optional_colon traits = trait_list { `Traits traits }
  | KNOWLEDGE optional_colon domains = domain_list { `Knowledge domains }
  | BEHAVIORS optional_colon behaviors = behavior_list { `Behaviors behaviors }
  | EVOLUTION optional_colon evolutions = evolution_list { `Evolution evolutions }

trait_list:
  | (* empty *) { [] }
  | name = IDENT COLON strength = FLOAT modifiers = trait_modifier_list optional_semicolon rest = trait_list { 
      { name; strength; modifiers } :: rest 
    }

trait_modifier_list:
  | (* empty *) { [] }
  | AMPLIFIES COLON target = IDENT MULTIPLY factor = FLOAT optional_semicolon rest = trait_modifier_list { 
      Types.Amplifies (target, factor) :: rest
    }
  | DECAY COLON rate = FLOAT DIVIDE unit = time_unit optional_semicolon rest = trait_modifier_list { 
      Types.Decay (rate, unit) :: rest
    }
  | WHEN COLON context = STRING optional_semicolon rest = trait_modifier_list { 
      Types.When (Types.Topic context) :: rest
    }
  | UNLESS COLON context = STRING optional_semicolon rest = trait_modifier_list { 
      Types.Unless (Types.Topic context) :: rest
    }

time_unit:
  | TIME_DAY { Types.Day }
  | TIME_WEEK { Types.Week }  
  | TIME_MONTH { Types.Month }
  | TIME_YEAR { Types.Year }

domain_list:
  | (* empty *) { [] }
  | domain = knowledge_domain rest = domain_list { domain :: rest }

knowledge_domain:
  | DOMAIN name = IDENT optional_colon items = domain_item_list optional_semicolon {
      let topics = ref [] in
      let connections = ref [] in
      List.iter (function
        | `Topic t -> topics := t :: !topics
        | `Connection c -> connections := c :: !connections
      ) items;
      { name; topics = List.rev !topics; connections = List.rev !connections }
    }

domain_item_list:
  | (* empty *) { [] }
  | name = IDENT COLON level = knowledge_level optional_semicolon rest = domain_item_list { 
      `Topic (name, level) :: rest 
    }
  | CONNECTS_TO COLON target = IDENT LPAREN strength = FLOAT RPAREN optional_semicolon rest = domain_item_list { 
      `Connection { from_domain = ""; to_domain = target; strength; evolution_rate = None } :: rest
    }

knowledge_level:
  | BEGINNER { Types.Beginner }
  | INTERMEDIATE { Types.Intermediate }
  | ADVANCED { Types.Advanced }  
  | EXPERT { Types.Expert }

behavior_list:
  | (* empty *) { [] }
  | LIST_ITEM WHEN condition = behavior_condition ARROW action = behavior_action optional_semicolon rest = behavior_list {
      { condition; action } :: rest
    }

behavior_condition:
  | trait = IDENT GT value = FLOAT { Types.Trait_above (trait, value) }
  | context = STRING { Types.Context_match context }

behavior_action:
  | PREFER value = STRING { Types.Prefer value }
  | SEEK value = STRING { Types.Seek value }
  | AVOID value = STRING { Types.Avoid value }

evolution_list:
  | (* empty *) { [] }
  | LIST_ITEM trigger = evolution_trigger ARROW eff = evolution_effect optional_semicolon rest = evolution_list {
      { trigger; action = eff } :: rest
    }

evolution_trigger:
  | LEARNS value = STRING { Types.Learns value }
  | AFTER count = FLOAT INTERACTIONS { Types.Interaction_count (Int.of_float count) }

evolution_effect:
  | trait = IDENT PLUS_EQUALS adj = FLOAT { 
      Types.Trait_adjust (trait, adj) 
    }
  | UNLOCK value = STRING { 
      Types.Unlock_domain value 
    }
  | CONNECT from_d = IDENT BIDIRECTIONAL to_d = IDENT LPAREN str = FLOAT RPAREN { 
      Types.Add_connection (from_d, to_d, str) 
    }