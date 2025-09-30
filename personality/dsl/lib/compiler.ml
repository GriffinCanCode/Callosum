open Base
open Stdio
open Ast

(** Compilation targets *)
type target = 
  | Json
  | Lua  
  | Prompt
  | Sql
  | Cypher

(** Compilation errors *)
type compiler_error = 
  | Invalid_trait_strength of string * float
  | Missing_domain of string
  | Circular_dependency of string list
  | Invalid_knowledge_level of string
  | Invalid_time_unit of string
  | Parse_errors of Types.parse_error list
  | Semantic_errors of Semantic.semantic_error list
  
let compiler_error_to_string = function
  | Invalid_trait_strength (name, value) -> 
      Printf.sprintf "Trait %s has invalid strength %f (must be 0.0-1.0)" name value
  | Missing_domain name -> 
      Printf.sprintf "Referenced domain %s not found" name  
  | Circular_dependency deps -> 
      Printf.sprintf "Circular dependency detected: %s" (String.concat ~sep:" -> " deps)
  | Invalid_knowledge_level level ->
      Printf.sprintf "Invalid knowledge level: %s (must be beginner|intermediate|advanced|expert)" level
  | Invalid_time_unit unit ->
      Printf.sprintf "Invalid time unit: %s (must be day|week|month|year)" unit
  | Parse_errors errors ->
      String.concat ~sep:"\n" (List.map errors ~f:Types.show_parse_error)
  | Semantic_errors errors ->
      String.concat ~sep:"\n" (List.map errors ~f:Semantic.error_to_string)

(** Validation functions *)
let validate_trait_strength (trait : Types.trait_spec) = 
  if Float.between trait.strength ~low:0.0 ~high:1.0 then Ok ()
  else Error (Invalid_trait_strength (trait.name, trait.strength))

let validate_knowledge_domains personality =
  let domain_names = List.map personality.knowledge ~f:(fun d -> d.name) in
  let unique_names = List.dedup_and_sort domain_names ~compare:String.compare in
  if List.length domain_names = List.length unique_names then Ok ()
  else Error (Missing_domain "Duplicate domain names detected")

let validate_personality personality = 
  let trait_errors = 
    List.filter_map personality.traits ~f:(fun trait ->
      match validate_trait_strength trait with
      | Ok () -> None  
      | Error e -> Some e)
  in
  let domain_validation = validate_knowledge_domains personality in
  let semantic_analysis = Semantic.analyze personality in
  
  let all_errors = 
    trait_errors @ 
    (match domain_validation with Ok () -> [] | Error e -> [e]) @
    (if List.is_empty semantic_analysis.errors then [] else [Semantic_errors semantic_analysis.errors])
  in
  
  (* Print warnings if any *)
  (if not (List.is_empty semantic_analysis.warnings) then
    let warning_strs = List.map semantic_analysis.warnings ~f:Semantic.warning_to_string in
    List.iter warning_strs ~f:(fun w -> printf "WARNING: %s\n" w));
  
  match all_errors with
  | [] -> Ok personality
  | errors -> Error errors

(** Helper functions for JSON compilation *)
let knowledge_level_to_string = function
  | Types.Beginner -> "beginner"
  | Types.Intermediate -> "intermediate" 
  | Types.Advanced -> "advanced"
  | Types.Expert -> "expert"

let time_unit_to_string = function
  | Types.Day -> "day"
  | Types.Week -> "week"
  | Types.Month -> "month"  
  | Types.Year -> "year"

let context_to_string = function
  | Types.Topic ctx -> ctx
  | Types.Situation ctx -> ctx
  | Types.Time_of_day ctx -> ctx
  | Types.Emotional_state ctx -> ctx

let trait_modifier_to_json modifier = 
  match modifier with
  | Types.Decay (rate, unit) -> 
      Printf.sprintf {|{"type": "decay", "rate": %f, "unit": "%s"}|} 
        rate (time_unit_to_string unit)
  | Types.When ctx -> 
      Printf.sprintf {|{"type": "when", "context": "%s"}|} (context_to_string ctx)
  | Types.Unless ctx -> 
      Printf.sprintf {|{"type": "unless", "context": "%s"}|} (context_to_string ctx)
  | Types.Amplifies (trait, factor) ->
      Printf.sprintf {|{"type": "amplifies", "trait": "%s", "factor": %f}|} trait factor
  | Types.Transforms_to (trait, factor, count) ->
      Printf.sprintf {|{"type": "transforms_to", "trait": "%s", "factor": %f, "count": %d}|} 
        trait factor count

(** JSON compilation *)  
let compile_to_json personality =
  match validate_personality personality with
  | Error errors -> Error errors
  | Ok p ->
      let traits_json = String.concat ~sep:", " (List.map p.traits ~f:(fun t ->
        let modifiers_json = String.concat ~sep:", " (List.map t.modifiers ~f:trait_modifier_to_json) in
        Printf.sprintf {|{"name": "%s", "strength": %f, "modifiers": [%s]}|} 
          t.name t.strength modifiers_json)) in
      
      let knowledge_json = String.concat ~sep:", " (List.map p.knowledge ~f:(fun d ->
        let topics_json = String.concat ~sep:", " (List.map d.topics ~f:(fun (name, level) ->
          Printf.sprintf {|{"name": "%s", "level": "%s"}|} name (knowledge_level_to_string level))) in
        Printf.sprintf {|{"name": "%s", "topics": [%s]}|} d.name topics_json)) in
      
      let json = Printf.sprintf {|{
  "name": "%s",
  "traits": [%s],
  "knowledge": [%s],
  "behaviors": [],
  "evolution": []
}|} p.name traits_json knowledge_json in
      Ok json

(** Lua compilation *)
let compile_to_lua personality = 
  match validate_personality personality with
  | Error errors -> Error errors
  | Ok p ->
      let lua = Printf.sprintf {|-- Generated Personality: %s
local personality = {}

personality.name = "%s"
personality.traits = {}
%s

personality.knowledge = {}
%s

return personality|} 
        p.name 
        p.name
        (String.concat ~sep:"\n" (List.map p.traits ~f:(fun t ->
          Printf.sprintf "personality.traits[\"%s\"] = %f" t.name t.strength)))
        (String.concat ~sep:"\n" (List.map p.knowledge ~f:(fun d ->
          Printf.sprintf "personality.knowledge[\"%s\"] = {}" d.name)))
      in
      Ok lua

(** Prompt compilation *)  
let compile_to_prompt personality context_hint = 
  match validate_personality personality with
  | Error errors -> Error errors
  | Ok p ->
      let trait_desc = String.concat ~sep:", " 
        (List.map p.traits ~f:(fun t -> 
          Printf.sprintf "%s (%.1f)" t.name t.strength)) in
      let knowledge_desc = String.concat ~sep:", "
        (List.map p.knowledge ~f:(fun d -> d.name)) in
      let prompt = Printf.sprintf {|You are %s, a personality with these traits: %s.
Your knowledge areas include: %s.
Context: %s

Respond in character based on your traits and knowledge.|} 
        p.name trait_desc knowledge_desc (Option.value context_hint ~default:"general") in
      Ok prompt

(** SQL compilation *)
let compile_to_sql personality =
  match validate_personality personality with
  | Error errors -> Error errors
  | Ok p ->
      let traits_sql = String.concat ~sep:",\n  " (List.mapi p.traits ~f:(fun i t ->
        Printf.sprintf "('%s', %d, '%s', %f, '%s')" 
          p.name i t.name t.strength (String.concat ~sep:";" (List.map t.modifiers ~f:show_trait_modifier)))) in
      
      let knowledge_sql = String.concat ~sep:",\n  " (List.fold p.knowledge ~init:[] ~f:(fun acc domain ->
        let domain_topics = List.mapi domain.topics ~f:(fun i (topic, level) ->
          Printf.sprintf "('%s', '%s', %d, '%s', '%s')" 
            p.name domain.name i topic (knowledge_level_to_string level)) in
        acc @ domain_topics)) in
      
      let behaviors_sql = String.concat ~sep:",\n  " (List.mapi p.behaviors ~f:(fun i behavior ->
        Printf.sprintf "('%s', %d, '%s', '%s')" 
          p.name i (show_behavior_condition behavior.condition) (show_behavior_action behavior.action))) in
      
      let evolution_sql = String.concat ~sep:",\n  " (List.mapi p.evolution ~f:(fun i evolution ->
        Printf.sprintf "('%s', %d, '%s', '%s')" 
          p.name i (show_evolution_trigger evolution.trigger) (show_evolution_effect evolution.action))) in
      
      let sql = Printf.sprintf {|-- Generated SQL for Personality: %s

-- Create tables if they don't exist
CREATE TABLE IF NOT EXISTS personalities (
  name VARCHAR(255) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS traits (
  personality_name VARCHAR(255),
  trait_order INTEGER,
  trait_name VARCHAR(255),
  strength FLOAT,
  modifiers TEXT,
  PRIMARY KEY (personality_name, trait_name),
  FOREIGN KEY (personality_name) REFERENCES personalities(name)
);

CREATE TABLE IF NOT EXISTS knowledge_topics (
  personality_name VARCHAR(255),
  domain_name VARCHAR(255),
  topic_order INTEGER,
  topic_name VARCHAR(255),
  level VARCHAR(50),
  PRIMARY KEY (personality_name, domain_name, topic_name),
  FOREIGN KEY (personality_name) REFERENCES personalities(name)
);

CREATE TABLE IF NOT EXISTS behaviors (
  personality_name VARCHAR(255),
  behavior_order INTEGER,
  condition_type TEXT,
  action_type TEXT,
  PRIMARY KEY (personality_name, behavior_order),
  FOREIGN KEY (personality_name) REFERENCES personalities(name)
);

CREATE TABLE IF NOT EXISTS evolution_rules (
  personality_name VARCHAR(255),
  rule_order INTEGER,
  trigger_type TEXT,
  effect_type TEXT,
  PRIMARY KEY (personality_name, rule_order),
  FOREIGN KEY (personality_name) REFERENCES personalities(name)
);

-- Insert data
INSERT INTO personalities (name) VALUES ('%s');

INSERT INTO traits (personality_name, trait_order, trait_name, strength, modifiers) VALUES
  %s;

INSERT INTO knowledge_topics (personality_name, domain_name, topic_order, topic_name, level) VALUES
  %s;

INSERT INTO behaviors (personality_name, behavior_order, condition_type, action_type) VALUES
  %s;

INSERT INTO evolution_rules (personality_name, rule_order, trigger_type, effect_type) VALUES
  %s;|} 
        p.name p.name traits_sql knowledge_sql behaviors_sql evolution_sql in
      Ok sql

(** Cypher compilation *)
let compile_to_cypher personality =
  match validate_personality personality with
  | Error errors -> Error errors
  | Ok p ->
      let traits_cypher = String.concat ~sep:", " (List.map p.traits ~f:(fun t ->
        Printf.sprintf "%s: %f" t.name t.strength)) in
      
      let domains_cypher = String.concat ~sep:"\n" (List.map p.knowledge ~f:(fun domain ->
        let topics_cypher = String.concat ~sep:", " (List.map domain.topics ~f:(fun (topic, level) ->
          Printf.sprintf "%s: '%s'" topic (knowledge_level_to_string level))) in
        Printf.sprintf "CREATE (d_%s:Domain {name: '%s', %s})" 
          (String.filter domain.name ~f:Char.is_alphanum) domain.name topics_cypher)) in
      
      let connections_cypher = String.concat ~sep:"\n" (List.fold p.knowledge ~init:[] ~f:(fun acc domain ->
        acc @ List.map domain.connections ~f:(fun conn ->
          Printf.sprintf "CREATE (d_%s)-[:CONNECTS {strength: %f}]->(d_%s)"
            (String.filter conn.from_domain ~f:Char.is_alphanum)
            conn.strength
            (String.filter conn.to_domain ~f:Char.is_alphanum)))) in
      
      let behaviors_cypher = String.concat ~sep:"\n" (List.mapi p.behaviors ~f:(fun i behavior ->
        Printf.sprintf "CREATE (b%d:Behavior {condition: '%s', action: '%s'})"
          i (show_behavior_condition behavior.condition) (show_behavior_action behavior.action))) in
      
      let evolution_cypher = String.concat ~sep:"\n" (List.mapi p.evolution ~f:(fun i evolution ->
        Printf.sprintf "CREATE (e%d:Evolution {trigger: '%s', effect: '%s'})"
          i (show_evolution_trigger evolution.trigger) (show_evolution_effect evolution.action))) in
      
      let cypher = Printf.sprintf {|// Generated Cypher for Personality: %s

// Create personality node
CREATE (p:Personality {name: '%s', %s})

// Create knowledge domains
%s

// Create connections
%s

// Create behaviors
%s

// Create evolution rules
%s

// Connect personality to its components
CREATE (p)-[:HAS_DOMAIN]->(d_%s)
CREATE (p)-[:HAS_BEHAVIOR]->(b0)
CREATE (p)-[:HAS_EVOLUTION]->(e0)|} 
        p.name p.name traits_cypher domains_cypher connections_cypher 
        behaviors_cypher evolution_cypher 
        (match p.knowledge with [] -> "none" | d::_ -> String.filter d.name ~f:Char.is_alphanum) in
      Ok cypher

(** Main compilation function *)
let compile personality target ?context () = 
  match target with
  | Json -> compile_to_json personality
  | Lua -> compile_to_lua personality
  | Prompt -> compile_to_prompt personality context
  | Sql -> compile_to_sql personality
  | Cypher -> compile_to_cypher personality
