open Base
open Types

(** Semantic analysis error types *)
type semantic_error =
  | Circular_dependency of string list
  | Trait_conflict of string * string * string  
  | Non_deterministic_evolution of string
  | Unreachable_behavior of string
  | Invalid_domain_reference of string
  | Conflicting_modifiers of string * string * string
  | Impossible_evolution_path of string * string
  | Orphaned_knowledge_connection of string * string
  | Contradictory_behavior of string * string
  | Unsafe_evolution of string * string
  | Dangerous_trait_modification of string * float
  [@@deriving show, eq]

type semantic_warning =
  | Unused_domain of string
  | Weak_connection of string * string * float
  | Redundant_modifier of string * string
  | Potential_trait_collision of string * string
  | Suspicious_evolution_rate of string * float
  | Behavior_pattern_conflict of string * string
  | Evolution_convergence_risk of string
  [@@deriving show, eq]

type analysis_result = {
  errors: semantic_error list;
  warnings: semantic_warning list;
  valid: bool;
} [@@deriving show, eq]

(** Helper functions for graph traversal *)
let rec find_cycles_dfs visited path graph node =
  if List.mem visited node ~equal:String.equal then
    if List.mem path node ~equal:String.equal then
      [List.drop_while path ~f:(fun x -> not (String.equal x node)) @ [node]]
    else []
  else
    let edges = List.Assoc.find graph node ~equal:String.equal |> Option.value ~default:[] in
    let new_visited = node :: visited in
    let new_path = node :: path in
    List.fold edges ~init:[] ~f:(fun acc neighbor ->
      acc @ find_cycles_dfs new_visited new_path graph neighbor)

(** Check for circular dependencies in knowledge domains *)
let check_circular_dependencies (personality : personality) =
  let build_dependency_graph domains =
    List.fold domains ~init:[] ~f:(fun acc domain ->
      let edges = List.map domain.connections ~f:(fun conn -> conn.to_domain) in
      (domain.name, edges) :: acc)
  in
  
  let graph = build_dependency_graph personality.knowledge in
  let all_domains = List.map personality.knowledge ~f:(fun d -> d.name) in
  
  List.fold all_domains ~init:[] ~f:(fun acc domain ->
    acc @ find_cycles_dfs [] [] graph domain)

(** Validate trait modifier conflicts *)
let check_trait_conflicts (personality : personality) =
  let find_conflicting_modifiers trait_name modifiers =
    let rec check_pairs = function
      | [] | [_] -> []
      | mod1 :: rest ->
          let conflicts = List.filter_map rest ~f:(fun mod2 ->
            match (mod1, mod2) with
            | (When ctx1, Unless ctx2) when equal_context ctx1 ctx2 ->
                Some (trait_name, show_trait_modifier mod1, show_trait_modifier mod2)
            | (Decay (rate1, unit1), Decay (rate2, unit2)) 
              when equal_time_unit unit1 unit2 && not (Float.equal rate1 rate2) ->
                Some (trait_name, show_trait_modifier mod1, show_trait_modifier mod2)
            | _ -> None) in
          conflicts @ check_pairs rest
    in
    check_pairs modifiers
  in
  
  List.fold personality.traits ~init:[] ~f:(fun acc trait ->
    acc @ find_conflicting_modifiers trait.name trait.modifiers)

(** Check evolution rule determinism *)
let check_evolution_determinism (personality : personality) =
  let group_by_trigger rules =
    List.fold rules ~init:[] ~f:(fun acc rule ->
      let trigger_key = show_evolution_trigger rule.trigger in
      match List.Assoc.find acc trigger_key ~equal:String.equal with
      | Some existing -> List.Assoc.add acc trigger_key (rule :: existing) ~equal:String.equal
      | None -> List.Assoc.add acc trigger_key [rule] ~equal:String.equal)
  in
  
  let grouped = group_by_trigger personality.evolution in
  List.fold grouped ~init:[] ~f:(fun acc (trigger, rules) ->
    if List.length rules > 1 then
      let different_effects = List.dedup_and_sort 
        (List.map rules ~f:(fun r -> show_evolution_effect r.action))
        ~compare:String.compare in
      if List.length different_effects > 1 then
        trigger :: acc
      else acc
    else acc)

(** Detect unreachable behaviors *)
let check_unreachable_behaviors (personality : personality) =
  let available_traits = List.map personality.traits ~f:(fun t -> t.name) in
  
  List.filter_map personality.behaviors ~f:(fun behavior ->
    match behavior.condition with
    | Trait_above (trait_name, _) ->
        if List.mem available_traits trait_name ~equal:String.equal then None
        else Some (Printf.sprintf "Behavior references non-existent trait: %s" trait_name)
    | _ -> None)

(** Validate domain references *)
let check_domain_references (personality : personality) =
  let available_domains = List.map personality.knowledge ~f:(fun d -> d.name) in
  let referenced_domains = 
    List.fold personality.knowledge ~init:[] ~f:(fun acc domain ->
      acc @ List.map domain.connections ~f:(fun conn -> conn.to_domain))
    @
    List.fold personality.evolution ~init:[] ~f:(fun acc evolution ->
      match evolution.trigger with
      | Time_in_domain (domain, _, _) -> domain :: acc
      | _ -> acc) @
    List.fold personality.evolution ~init:[] ~f:(fun acc evolution ->
      match evolution.action with  
      | Unlock_domain domain -> domain :: acc
      | Add_connection (from_d, to_d, _) -> [from_d; to_d] @ acc
      | _ -> acc)
  in
  
  List.filter referenced_domains ~f:(fun domain ->
    not (List.mem available_domains domain ~equal:String.equal))

(** Check for conflicting modifiers within single trait *)
let check_modifier_conflicts (personality : personality) =
  List.fold personality.traits ~init:[] ~f:(fun acc trait ->
    let modifiers = trait.modifiers in
    let conflicts = List.fold modifiers ~init:[] ~f:(fun inner_acc mod1 ->
      List.fold modifiers ~init:inner_acc ~f:(fun inner_acc2 mod2 ->
        if not (equal_trait_modifier mod1 mod2) then
          match (mod1, mod2) with
          | (When ctx1, Unless ctx2) when equal_context ctx1 ctx2 ->
              (trait.name, show_trait_modifier mod1, show_trait_modifier mod2) :: inner_acc2
          | _ -> inner_acc2
        else inner_acc2)) in
    conflicts @ acc)

(** Check behavior rule consistency *)
let check_behavior_consistency (personality : personality) =
  let find_contradictory_behaviors (behaviors : behavior_rule list) =
    let rec check_pairs = function
      | [] | [_] -> []
      | (b1 : behavior_rule) :: rest ->
          let contradictions = List.filter_map rest ~f:(fun (b2 : behavior_rule) ->
            match (b1.action, b2.action) with
            | (Prefer value1, Avoid value2) when String.equal value1 value2 ->
                Some (show_behavior_action b1.action, show_behavior_action b2.action)
            | (Avoid value1, Prefer value2) when String.equal value1 value2 ->
                Some (show_behavior_action b1.action, show_behavior_action b2.action)
            | (Seek value1, Avoid value2) when String.equal value1 value2 ->
                Some (show_behavior_action b1.action, show_behavior_action b2.action)
            | (Set_style (style1, val1), Set_style (style2, val2)) 
              when String.equal style1 style2 && not (String.equal val1 val2) ->
                Some (show_behavior_action b1.action, show_behavior_action b2.action)
            | _ -> None) in
          contradictions @ check_pairs rest
    in
    check_pairs behaviors
  in
  find_contradictory_behaviors personality.behaviors

(** Check evolution rule safety *)
let check_evolution_safety (personality : personality) =
  let check_dangerous_modifications rules =
    List.filter_map rules ~f:(fun rule ->
      match rule.action with
      | Types.Trait_adjust (trait_name, delta) when Float.(abs delta > 0.8) ->
          Some (trait_name, Printf.sprintf "Large trait adjustment: %f" delta)
      | _ -> None)
  in
  
  let check_unsafe_paths rules =
    List.filter_map rules ~f:(fun rule ->
      match rule.action with
      | Types.Trait_adjust (trait_name, delta) ->
          let current_trait = List.find personality.traits ~f:(fun t -> String.equal t.name trait_name) in
          (match current_trait with
          | Some t ->
              let new_strength = Float.(t.strength + delta) in
              if Float.(new_strength < 0.0) || Float.(new_strength > 1.0) then
                Some (trait_name, Printf.sprintf "Trait would go out of bounds: %f -> %f" t.strength new_strength)
              else None
          | _ -> None)
      | Types.Add_connection (from_d, to_d, _) ->
          let from_exists = List.exists personality.knowledge ~f:(fun d -> String.equal d.name from_d) in
          let to_exists = List.exists personality.knowledge ~f:(fun d -> String.equal d.name to_d) in
          if not (from_exists && to_exists) then
            Some (from_d, Printf.sprintf "Connection to non-existent domain: %s -> %s" from_d to_d)
          else None
      | _ -> None)
  in
  
  let dangerous = check_dangerous_modifications personality.evolution in
  let unsafe = check_unsafe_paths personality.evolution in
  dangerous @ unsafe

(** Generate warnings for suspicious patterns *)
let generate_warnings (personality : personality) =
  let unused_domains = 
    let referenced_domains = 
      List.fold personality.knowledge ~init:[] ~f:(fun acc (domain : knowledge_domain) ->
        acc @ List.map domain.connections ~f:(fun conn -> conn.to_domain)) in
    let unused_domain_list = List.filter personality.knowledge ~f:(fun (domain : knowledge_domain) ->
      not (List.mem referenced_domains domain.name ~equal:String.equal)) in
    List.map unused_domain_list ~f:(fun d -> Unused_domain d.name)
  in
  
  let weak_connections = 
    List.fold personality.knowledge ~init:[] ~f:(fun acc domain ->
      let weak_conns = List.filter domain.connections ~f:(fun conn -> Float.(conn.strength < 0.3)) in
      acc @ List.map weak_conns ~f:(fun conn -> Weak_connection (conn.from_domain, conn.to_domain, conn.strength)))
  in
  
  let redundant_modifiers =
    List.fold personality.traits ~init:[] ~f:(fun acc trait ->
      let decay_modifiers = List.filter trait.modifiers ~f:(function Decay _ -> true | _ -> false) in
      if List.length decay_modifiers > 1 then
        (Redundant_modifier (trait.name, "multiple decay modifiers")) :: acc
      else acc)
  in
  
  let suspicious_evolution = 
    List.filter_map personality.evolution ~f:(fun evolution ->
      match evolution.action with
      | Trait_adjust (trait_name, delta) when Float.(abs delta > 0.5) ->
          Some (Suspicious_evolution_rate (trait_name, delta))
      | _ -> None)
  in
  
  unused_domains @ weak_connections @ redundant_modifiers @ suspicious_evolution

(** Main semantic analysis function *)
let analyze (personality : personality) =
  let circular_deps = check_circular_dependencies personality in
  let trait_conflicts = check_trait_conflicts personality in  
  let non_deterministic = check_evolution_determinism personality in
  let unreachable = check_unreachable_behaviors personality in
  let invalid_domains = check_domain_references personality in
  let modifier_conflicts = check_modifier_conflicts personality in
  let behavior_contradictions = check_behavior_consistency personality in
  let evolution_safety = check_evolution_safety personality in
  
  let errors = 
    List.map circular_deps ~f:(fun cycle -> Circular_dependency cycle) @
    List.map trait_conflicts ~f:(fun (trait, mod1, mod2) -> Trait_conflict (trait, mod1, mod2)) @
    List.map non_deterministic ~f:(fun trigger -> Non_deterministic_evolution trigger) @
    List.map unreachable ~f:(fun behavior -> Unreachable_behavior behavior) @
    List.map invalid_domains ~f:(fun domain -> Invalid_domain_reference domain) @
    List.map modifier_conflicts ~f:(fun (trait, mod1, mod2) -> Conflicting_modifiers (trait, mod1, mod2)) @
    List.map behavior_contradictions ~f:(fun (action1, action2) -> Contradictory_behavior (action1, action2)) @
    List.map evolution_safety ~f:(fun (trait, reason) -> Unsafe_evolution (trait, reason))
  in
  
  let warnings = generate_warnings personality in
  
  {
    errors;
    warnings;
    valid = List.is_empty errors;
  }

(** Convert semantic errors to user-friendly strings *)
let error_to_string = function
  | Circular_dependency cycle ->
      Printf.sprintf "Circular dependency in knowledge domains: %s" (String.concat cycle ~sep:" -> ")
  | Trait_conflict (trait, mod1, mod2) ->
      Printf.sprintf "Conflicting modifiers for trait '%s': %s conflicts with %s" trait mod1 mod2
  | Non_deterministic_evolution trigger ->
      Printf.sprintf "Non-deterministic evolution: trigger '%s' has multiple conflicting effects" trigger
  | Unreachable_behavior behavior ->
      Printf.sprintf "Unreachable behavior: %s" behavior
  | Invalid_domain_reference domain ->
      Printf.sprintf "Reference to undefined knowledge domain: %s" domain
  | Conflicting_modifiers (trait, mod1, mod2) ->
      Printf.sprintf "Trait '%s' has conflicting modifiers: %s and %s" trait mod1 mod2
  | Impossible_evolution_path (from_d, to_d) ->
      Printf.sprintf "Impossible evolution path from %s to %s" from_d to_d
  | Orphaned_knowledge_connection (from_d, to_d) ->
      Printf.sprintf "Orphaned connection: %s -> %s (one domain missing)" from_d to_d
  | Contradictory_behavior (action1, action2) ->
      Printf.sprintf "Contradictory behaviors: %s conflicts with %s" action1 action2
  | Unsafe_evolution (trait, reason) ->
      Printf.sprintf "Unsafe evolution for trait '%s': %s" trait reason
  | Dangerous_trait_modification (trait, delta) ->
      Printf.sprintf "Dangerous trait modification for '%s': %f (exceeds safety threshold)" trait delta

(** Convert semantic warnings to user-friendly strings *)
let warning_to_string = function
  | Unused_domain domain ->
      Printf.sprintf "Warning: Domain '%s' is defined but never referenced" domain
  | Weak_connection (from_d, to_d, strength) ->
      Printf.sprintf "Warning: Weak connection %s -> %s (strength: %.2f)" from_d to_d strength
  | Redundant_modifier (trait, description) ->
      Printf.sprintf "Warning: Redundant modifier in trait '%s': %s" trait description
  | Potential_trait_collision (trait1, trait2) ->
      Printf.sprintf "Warning: Potential collision between traits '%s' and '%s'" trait1 trait2
  | Suspicious_evolution_rate (trait, rate) ->
      Printf.sprintf "Warning: Large evolution rate for trait '%s': %.2f" trait rate
  | Behavior_pattern_conflict (pattern1, pattern2) ->
      Printf.sprintf "Warning: Behavior pattern conflict: %s vs %s" pattern1 pattern2
  | Evolution_convergence_risk trait ->
      Printf.sprintf "Warning: Evolution convergence risk for trait '%s'" trait
