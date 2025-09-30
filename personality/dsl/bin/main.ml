open Base
open Stdio
open Dsl_parser


let demonstrate_compilation personality target_name target =
  match Compiler.compile personality target () with
  | Ok output -> 
      printf "\n%s output:\n%s\n" target_name output
  | Error errors -> 
      printf "\n%s compilation errors:\n" target_name;
      List.iter errors ~f:(fun e -> 
        printf "  - %s\n" (Compiler.compiler_error_to_string e)
      )

let () =
  printf "Callosum DSL Parser - Advanced Features v0.1.0\n";
  printf "==============================================\n\n";
  
  printf "Parsing comprehensive example personality from DSL...\n";
  
  (* Parse an actual DSL personality *)
  let dsl = {|personality "Creative Technologist" {
  traits {
    curiosity: 0.8 with decay(0.05/month), when("learning");
    analytical: 0.7 with amplifies("problem_solving", 1.2);
    creativity: 0.9 with unless("stressed");
  }
  
  knowledge {
    domain("programming") {
      ocaml: expert;
      python: advanced;
      rust: intermediate;
    }
    
    domain("design") {
      ui_ux: advanced;
      visual_design: intermediate;
      "programming" connects_to "design" with 0.8;
    }
  }
  
  behaviors {
    when curiosity > 0.7 -> seek("new technologies");
    when analytical > 0.6 -> prefer("systematic approach");
    when tired() -> avoid("complex problems");
  }
  
  evolution {
    if learns("new language") then trait("curiosity") += 0.1;
    if interactions(50) then unlock_domain("philosophy");
    if learns("design pattern") then add_connection("programming", "design", 0.9);
  }
}|} in

  let parsed_with_traits = match Ast.parse_personality_from_string dsl with
    | Ok personality -> 
        printf "✓ Successfully parsed DSL personality: %s\n" personality.Types.name;
        personality
    | Error errors ->
        printf "❌ Parse errors:\n";
        List.iter errors ~f:(fun e -> 
          printf "  - %s at line %d:%d\n" e.Types.message e.Types.location.start_line e.Types.location.start_col
        );
        (* Fall back to manual creation for demo *)
        let fallback = Ast.create_personality "Creative Technologist (fallback)" in
        let trait = Types.{ name = "curiosity"; strength = 0.8; modifiers = [] } in
        Ast.add_trait fallback trait
  in
  
  printf "  - Traits: %d\n" (List.length parsed_with_traits.Types.traits);
  printf "  - Knowledge domains: %d\n" (List.length parsed_with_traits.Types.knowledge);  
  printf "  - Behaviors: %d\n" (List.length parsed_with_traits.Types.behaviors);
  printf "  - Evolution rules: %d\n" (List.length parsed_with_traits.Types.evolution);
  
  (* Demonstrate different compilation targets *)
  demonstrate_compilation parsed_with_traits "JSON" Compiler.Json;
  demonstrate_compilation parsed_with_traits "Lua" Compiler.Lua;
  demonstrate_compilation parsed_with_traits "Prompt" Compiler.Prompt;
      
  printf "\nTesting DSL error handling...\n";
  (* Test invalid DSL syntax *)
  let invalid_dsl = {|personality "Invalid Test" {
  traits {
    invalid_trait: 1.5;  // Invalid strength > 1.0
    malformed: ;  // Missing value
  }
}|} in
  
  (match Ast.parse_personality_from_string invalid_dsl with
  | Ok personality -> 
      (* Even if parsing succeeds, validation should catch the error *)
      (match Compiler.compile personality Compiler.Json () with
      | Ok _ -> printf "❌ Should have failed validation\n"
      | Error errors -> 
          printf "✓ Caught validation errors during compilation:\n";
          List.iter errors ~f:(fun e -> 
            printf "  - %s\n" (Compiler.compiler_error_to_string e)
          ))
  | Error errors -> 
      printf "✓ Caught parse errors:\n";
      List.iter errors ~f:(fun e -> 
        printf "  - %s at line %d:%d\n" e.Types.message e.Types.location.start_line e.Types.location.start_col
      ))
