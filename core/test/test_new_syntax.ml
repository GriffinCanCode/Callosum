open Alcotest
open Dsl_parser.Ast

let test_simple_personality () =
  let input = {|personality: "Test Personality"

traits:
  helpfulness: 0.9

knowledge:
  domain conversation:
    active_listening: expert

behaviors:
  - when helpfulness > 0.8 → seek "ways to help"

evolution:
  - learns "user_preference" → helpfulness += 0.1|} in
  match parse_personality_from_string input with
  | Ok personality ->
    check string "personality name" "Test Personality" personality.name;
    check int "traits count" 1 (List.length personality.traits);
    check int "knowledge count" 1 (List.length personality.knowledge);
    check int "behaviors count" 1 (List.length personality.behaviors);
    check int "evolution count" 1 (List.length personality.evolution)
  | Error errors ->
    let msg = String.concat "; " (List.map (fun e -> e.message) errors) in
    fail ("Parse failed: " ^ msg)

let test_empty_personality () =
  let input = {|personality: "Empty Personality"|} in
  match parse_personality_from_string input with
  | Ok personality ->
    check string "personality name" "Empty Personality" personality.name;
    check int "traits count" 0 (List.length personality.traits);
    check int "knowledge count" 0 (List.length personality.knowledge);
    check int "behaviors count" 0 (List.length personality.behaviors);
    check int "evolution count" 0 (List.length personality.evolution)
  | Error errors ->
    let msg = String.concat "; " (List.map (fun e -> e.message) errors) in
    fail ("Parse failed: " ^ msg)

let () =
  run "New Syntax Tests" [
    "simple personality", [ test_case "parse simple personality" `Quick test_simple_personality ];
    "empty personality", [ test_case "parse empty personality" `Quick test_empty_personality ];
  ]
