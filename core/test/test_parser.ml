open Base
open Dsl_parser

(* Test personality creation *)
let test_personality_creation () = 
  let personality = Ast.create_personality "Test" in
  Alcotest.(check string) "personality name" "Test" personality.name;
  Alcotest.(check int) "empty traits" 0 (List.length personality.traits)

let test_trait_addition () = 
  let personality = Ast.create_personality "Test" in
  let trait = Types.{ name = "creativity"; strength = 0.7; modifiers = [] } in
  let updated = Ast.add_trait personality trait in
  Alcotest.(check int) "one trait" 1 (List.length updated.traits);
  let added_trait = List.hd_exn updated.traits in
  Alcotest.(check string) "trait name" "creativity" added_trait.name;
  Alcotest.(check (float 0.01)) "trait strength" 0.7 added_trait.strength

(* Test basic DSL parsing *)
let test_simple_personality_parsing () =
  let dsl = {|personality: "Creative Thinker"

traits:
  creativity: 0.8
  analytical: 0.6|} in
  match Ast.parse_personality_from_string dsl with
  | Ok personality ->
      Alcotest.(check string) "personality name" "Creative Thinker" personality.Types.name;
      Alcotest.(check int) "trait count" 2 (List.length personality.Types.traits);
      let trait_names = List.map personality.Types.traits ~f:(fun t -> t.Types.name) in
      Alcotest.(check bool) "has creativity trait" true (List.mem trait_names "creativity" ~equal:String.equal);
      Alcotest.(check bool) "has analytical trait" true (List.mem trait_names "analytical" ~equal:String.equal)
  | Error errors ->
      let error_messages = String.concat ~sep:"; " (List.map errors ~f:(fun e -> e.message)) in
      Alcotest.fail ("Parse failed: " ^ error_messages)

(* Test trait modifiers *)
let test_trait_modifiers () =
  let dsl = {|personality: "Modifier Test"

traits:
  focus: 0.7
    when: "work"|} in
  match Ast.parse_personality_from_string dsl with
  | Ok personality ->
      Alcotest.(check int) "trait count" 1 (List.length personality.Types.traits);
      let trait = List.hd_exn personality.Types.traits in
      Alcotest.(check string) "trait name" "focus" trait.Types.name;
      Alcotest.(check (float 0.01)) "trait strength" 0.7 trait.Types.strength;
      Alcotest.(check int) "modifier count" 1 (List.length trait.Types.modifiers)
  | Error errors ->
      let error_messages = String.concat ~sep:"; " (List.map errors ~f:(fun e -> e.message)) in
      Alcotest.fail ("Parse failed: " ^ error_messages)

(* Test knowledge domains *)
let test_knowledge_domains () =
  let dsl = {|personality: "Knowledge Test"

knowledge:
  domain programming:
    ocaml: expert
    python: intermediate|} in
  match Ast.parse_personality_from_string dsl with
  | Ok personality ->
      Alcotest.(check int) "domain count" 1 (List.length personality.Types.knowledge);
      let domain = List.hd_exn personality.Types.knowledge in
      Alcotest.(check string) "domain name" "programming" domain.Types.name;
      Alcotest.(check int) "topic count" 2 (List.length domain.Types.topics)
  | Error errors ->
      let error_messages = String.concat ~sep:"; " (List.map errors ~f:(fun e -> e.message)) in
      Alcotest.fail ("Parse failed: " ^ error_messages)

(* Test error handling *)
let test_invalid_syntax () =
  let dsl = {|
    personality "Invalid" {
      traits {
        invalid_trait: 1.5;  // Invalid strength > 1.0
      }
    }
  |} in
  match Ast.parse_personality_from_string dsl with
  | Ok personality ->
      (* Should parse but fail validation *)
      (match Compiler.compile personality Json () with
      | Ok _ -> Alcotest.fail "Should fail validation"
      | Error _ -> ()) (* Expected *)
  | Error _ -> () (* Also acceptable - parse error *)

let test_json_compilation () = 
  let personality = Ast.create_personality "Test" in
  let trait = Types.{ name = "analytical"; strength = 0.6; modifiers = [] } in
  let personality_with_trait = Ast.add_trait personality trait in
  match Compiler.compile personality_with_trait Json () with
  | Ok json -> 
      Alcotest.(check bool) "json contains name" true (String.is_substring json ~substring:"Test");
      Alcotest.(check bool) "json contains trait" true (String.is_substring json ~substring:"analytical")
  | Error _ -> Alcotest.fail "JSON compilation should succeed"

let test_lua_compilation () = 
  let personality = Ast.create_personality "Test" in
  let trait = Types.{ name = "creativity"; strength = 0.7; modifiers = [] } in
  let personality_with_trait = Ast.add_trait personality trait in
  match Compiler.compile personality_with_trait Lua () with
  | Ok lua -> 
      Alcotest.(check bool) "lua contains name" true (String.is_substring lua ~substring:"Test");
      Alcotest.(check bool) "lua contains trait" true (String.is_substring lua ~substring:"creativity")
  | Error _ -> Alcotest.fail "Lua compilation should succeed"

let test_trait_validation () = 
  let personality = Ast.create_personality "Test" in
  let invalid_trait = Types.{ name = "invalid"; strength = 1.5; modifiers = [] } in
  let personality_with_invalid = Ast.add_trait personality invalid_trait in
  match Compiler.compile personality_with_invalid Json () with
  | Ok _ -> Alcotest.fail "Should fail with invalid trait strength"
  | Error errors -> 
      Alcotest.(check bool) "has validation error" true (List.length errors > 0)

(* Test semantic analysis *)
let test_circular_dependency () =
  let domain1 = Types.{
    name = "A";
    topics = [];
    connections = [{from_domain = "A"; to_domain = "B"; strength = 0.5; evolution_rate = None}];
  } in
  let domain2 = Types.{
    name = "B"; 
    topics = [];
    connections = [{from_domain = "B"; to_domain = "A"; strength = 0.5; evolution_rate = None}];
  } in
  let personality = { (Ast.create_personality "Test") with knowledge = [domain1; domain2] } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "detects circular dependency" false analysis.valid;
  let has_circular_error = List.exists analysis.errors ~f:(function 
    | Semantic.Circular_dependency _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has circular dependency error" true has_circular_error

let test_trait_conflicts () =
  let conflicting_modifiers = [
    Types.When (Types.Topic "work");
    Types.Unless (Types.Topic "work");
  ] in
  let trait = Types.{ name = "focus"; strength = 0.7; modifiers = conflicting_modifiers } in
  let personality = Ast.add_trait (Ast.create_personality "Test") trait in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "detects trait conflict" false analysis.valid;
  let has_conflict_error = List.exists analysis.errors ~f:(function 
    | Semantic.Trait_conflict _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has trait conflict error" true has_conflict_error

let test_evolution_determinism () =
  let trigger = Types.Learns "programming" in
  let evolution1 = Types.{ trigger; action = Types.Trait_adjust ("analytical", 0.1) } in
  let evolution2 = Types.{ trigger; action = Types.Trait_adjust ("analytical", 0.2) } in
  let personality = { (Ast.create_personality "Test") with evolution = [evolution1; evolution2] } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "detects non-deterministic evolution" false analysis.valid;
  let has_nondeterministic_error = List.exists analysis.errors ~f:(function 
    | Semantic.Non_deterministic_evolution _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has non-deterministic evolution error" true has_nondeterministic_error

let test_unreachable_behavior () =
  let behavior = Types.{ 
    condition = Types.Trait_above ("nonexistent", 0.5);
    action = Types.Prefer "thinking";
  } in
  let personality = { (Ast.create_personality "Test") with behaviors = [behavior] } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "detects unreachable behavior" false analysis.valid;
  let has_unreachable_error = List.exists analysis.errors ~f:(function 
    | Semantic.Unreachable_behavior _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has unreachable behavior error" true has_unreachable_error

let test_domain_references () =
  let evolution = Types.{ 
    trigger = Types.Time_in_domain ("nonexistent", Types.Month, 6);
    action = Types.Trait_adjust ("learning", 0.1);
  } in
  let personality = { (Ast.create_personality "Test") with evolution = [evolution] } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "detects invalid domain reference" false analysis.valid;
  let has_domain_error = List.exists analysis.errors ~f:(function 
    | Semantic.Invalid_domain_reference _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has invalid domain reference error" true has_domain_error

let test_warnings_generation () =
  let unused_domain = Types.{
    name = "unused";
    topics = [("topic1", Types.Beginner)];
    connections = [];
  } in
  let weak_connection_domain = Types.{
    name = "weak";
    topics = [];
    connections = [{from_domain = "weak"; to_domain = "unused"; strength = 0.1; evolution_rate = None}];
  } in
  let personality = { (Ast.create_personality "Test") with 
    knowledge = [unused_domain; weak_connection_domain] } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "generates warnings" true (List.length analysis.warnings > 0);
  let has_unused_warning = List.exists analysis.warnings ~f:(function 
    | Semantic.Unused_domain _ -> true 
    | _ -> false) in
  let has_weak_warning = List.exists analysis.warnings ~f:(function 
    | Semantic.Weak_connection _ -> true 
    | _ -> false) in
  Alcotest.(check bool) "has unused domain warning" true has_unused_warning;
  Alcotest.(check bool) "has weak connection warning" true has_weak_warning

let test_valid_personality_passes () =
  let domain = Types.{
    name = "programming";
    topics = [("ocaml", Types.Advanced); ("python", Types.Intermediate)];
    connections = [];
  } in
  let trait = Types.{ name = "analytical"; strength = 0.7; modifiers = [] } in
  let behavior = Types.{ 
    condition = Types.Trait_above ("analytical", 0.5);
    action = Types.Prefer "logical reasoning";
  } in
  let evolution = Types.{ 
    trigger = Types.Time_in_domain ("programming", Types.Month, 3);
    action = Types.Trait_adjust ("analytical", 0.1);
  } in
  let personality = { (Ast.create_personality "Test") with 
    knowledge = [domain];
    traits = [trait];
    behaviors = [behavior];
    evolution = [evolution];
  } in
  let analysis = Semantic.analyze personality in
  Alcotest.(check bool) "valid personality passes" true analysis.valid;
  Alcotest.(check int) "no errors" 0 (List.length analysis.errors)

(* Test comprehensive DSL *)
let test_full_personality () =
  let dsl = {|personality: "Complete Test"

traits:
  creativity: 0.8
  analytical: 0.6
  
knowledge:
  domain science:
    physics: advanced
    chemistry: intermediate
  
behaviors:
  - when "tired" → prefer "rest"
  - when creativity > 0.7 → seek "creative projects"
  
evolution:
  - learns "new skill" → curiosity += 0.1
  - after 10.0 interactions → unlock "philosophy"|} in
  match Ast.parse_personality_from_string dsl with
  | Ok personality ->
      Alcotest.(check string) "personality name" "Complete Test" personality.Types.name;
      Alcotest.(check int) "trait count" 2 (List.length personality.Types.traits);
      Alcotest.(check int) "domain count" 1 (List.length personality.Types.knowledge);
      Alcotest.(check int) "behavior count" 2 (List.length personality.Types.behaviors);
      Alcotest.(check int) "evolution count" 2 (List.length personality.Types.evolution)
  | Error errors ->
      let error_messages = String.concat ~sep:"; " (List.map errors ~f:(fun e -> e.message)) in
      Alcotest.fail ("Parse failed: " ^ error_messages)

let () = 
  let open Alcotest in
  run "DSL Parser Tests" [
    "personality", [
      test_case "create personality" `Quick test_personality_creation;
      test_case "add trait" `Quick test_trait_addition;
    ];
    "parsing", [
      test_case "simple personality" `Quick test_simple_personality_parsing;
      test_case "trait modifiers" `Quick test_trait_modifiers;
      test_case "knowledge domains" `Quick test_knowledge_domains;
      test_case "full personality" `Quick test_full_personality;
    ];
    "error_handling", [
      test_case "invalid syntax" `Quick test_invalid_syntax;
    ];
    "compiler", [
      test_case "json compilation" `Quick test_json_compilation;
      test_case "lua compilation" `Quick test_lua_compilation;
      test_case "trait validation" `Quick test_trait_validation;
    ];
    "semantic_analysis", [
      test_case "circular dependency" `Quick test_circular_dependency;
      test_case "trait conflicts" `Quick test_trait_conflicts;
      test_case "evolution determinism" `Quick test_evolution_determinism;
      test_case "unreachable behavior" `Quick test_unreachable_behavior;
      test_case "domain references" `Quick test_domain_references;
      test_case "warnings generation" `Quick test_warnings_generation;
      test_case "valid personality passes" `Quick test_valid_personality_passes;
    ];
  ]
