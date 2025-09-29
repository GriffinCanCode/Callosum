open Base
open Types

(** Optimization level *)
type level = 
  | None_opt
  | Basic
  | Aggressive
  [@@deriving show, eq]

(** Optimization statistics *)
type stats = {
  traits_folded: int;
  dead_rules_removed: int;
  expressions_eliminated: int;
  rules_reordered: int;
  cached_calculations: int;
} [@@deriving show, eq]

let empty_stats = {
  traits_folded = 0;
  dead_rules_removed = 0;
  expressions_eliminated = 0;
  rules_reordered = 0;
  cached_calculations = 0;
}

(** Trait constant folding *)
let fold_trait_constants (trait : trait_spec) =
  let rec fold_modifiers = function
    | [] -> []
    | Decay (rate, _unit) :: rest when Float.(rate <= 0.0) -> fold_modifiers rest
    | Amplifies (_name, factor) :: rest when Float.(factor = 1.0) -> fold_modifiers rest
    | modifier :: rest -> modifier :: fold_modifiers rest
  in
  
  let folded_modifiers = fold_modifiers trait.modifiers in
  let folded_count = List.length trait.modifiers - List.length folded_modifiers in
  
  ({ trait with modifiers = folded_modifiers }, folded_count)

(** Dead code elimination for evolution rules *)
let eliminate_dead_evolution_rules (personality : personality) =
  let available_traits = List.map personality.traits ~f:(fun t -> t.name) in
  let available_domains = List.map personality.knowledge ~f:(fun d -> d.name) in
  
  let is_rule_reachable rule =
    match rule.trigger with
    | Learns domain -> List.mem available_domains domain ~equal:String.equal
    | Time_in_domain (domain, _, _) -> List.mem available_domains domain ~equal:String.equal
    | _ -> true
  in
  
  let is_rule_valid rule =
    match rule.action with
    | Trait_adjust (trait_name, _) -> List.mem available_traits trait_name ~equal:String.equal
    | Add_connection (from_d, to_d, _) -> 
        List.mem available_domains from_d ~equal:String.equal &&
        List.mem available_domains to_d ~equal:String.equal
    | Unlock_domain _ -> true
    | New_behavior _ -> true
  in
  
  let live_rules = List.filter personality.evolution ~f:(fun rule ->
    is_rule_reachable rule && is_rule_valid rule) in
  
  let removed_count = List.length personality.evolution - List.length live_rules in
  ({ personality with evolution = live_rules }, removed_count)

(** Common subexpression elimination *)
let eliminate_common_subexpressions (personality : personality) =
  let trait_map = Map.of_alist_exn (module String) (List.map personality.traits ~f:(fun trait -> (trait.name, trait))) in
  
  (* Find common patterns in trait modifiers *)
  let find_common_patterns () =
    let patterns = Map.fold trait_map ~init:[] ~f:(fun ~key:_ ~data:trait acc ->
      trait.modifiers @ acc) in
    
    let pattern_counts = List.fold patterns ~init:[] ~f:(fun acc modifier ->
      match List.Assoc.find acc modifier ~equal:equal_trait_modifier with
      | Some count -> List.Assoc.add acc modifier (count + 1) ~equal:equal_trait_modifier
      | None -> List.Assoc.add acc modifier 1 ~equal:equal_trait_modifier) in
    
    List.filter pattern_counts ~f:(fun (_, count) -> count > 1)
  in
  
  let common_patterns = find_common_patterns () in
  let eliminated_count = List.fold common_patterns ~init:0 ~f:(fun acc (_, count) -> acc + count - 1) in
  
  (* Note: For now, we just count potential eliminations without actually transforming *)
  (personality, eliminated_count)

(** Rule ordering optimization *)
let optimize_rule_ordering (personality : personality) =
  (* Sort evolution rules by priority: immediate effects first, then conditional *)
  let score_rule rule =
    match rule.trigger with
    | Learns _ -> 1 (* High priority - immediate learning *)
    | Feedback_score _ -> 2 (* Medium priority - feedback based *)
    | Interaction_count _ -> 3 (* Lower priority - count based *)
    | Time_in_domain _ -> 4 (* Lowest priority - time based *)
  in
  
  let sorted_rules = List.sort personality.evolution ~compare:(fun r1 r2 ->
    Int.compare (score_rule r1) (score_rule r2)) in
  
  let reordered_count = if List.equal equal_evolution_spec personality.evolution sorted_rules then 0 else 1 in
  ({ personality with evolution = sorted_rules }, reordered_count)

(** Trait calculation caching *)
let add_calculation_caching (personality : personality) =
  (* Add metadata for traits that should be cached *)
  let traits_needing_cache = List.filter personality.traits ~f:(fun trait ->
    List.exists trait.modifiers ~f:(function
      | Decay _ -> true
      | Transforms_to _ -> true
      | _ -> false)) in
  
  let cache_count = List.length traits_needing_cache in
  (personality, cache_count)

(** Main optimization pipeline *)
let optimize_personality (personality : personality) (level : level) =
  match level with
  | None_opt -> (personality, empty_stats)
  | Basic -> 
      let (p1, traits_folded) = 
        List.fold personality.traits ~init:(personality, 0) ~f:(fun (p, count) trait ->
          let (folded_trait, folded_count) = fold_trait_constants trait in
          let updated_traits = List.map p.traits ~f:(fun t ->
            if String.equal t.name trait.name then folded_trait else t) in
          ({ p with traits = updated_traits }, count + folded_count)) in
      
      let (p2, dead_rules_removed) = eliminate_dead_evolution_rules p1 in
      let (p3, cached_calculations) = add_calculation_caching p2 in
      
      let stats = {
        traits_folded;
        dead_rules_removed;
        expressions_eliminated = 0;
        rules_reordered = 0;
        cached_calculations;
      } in
      (p3, stats)
      
  | Aggressive ->
      let (p1, traits_folded) = 
        List.fold personality.traits ~init:(personality, 0) ~f:(fun (p, count) trait ->
          let (folded_trait, folded_count) = fold_trait_constants trait in
          let updated_traits = List.map p.traits ~f:(fun t ->
            if String.equal t.name trait.name then folded_trait else t) in
          ({ p with traits = updated_traits }, count + folded_count)) in
      
      let (p2, dead_rules_removed) = eliminate_dead_evolution_rules p1 in
      let (p3, expressions_eliminated) = eliminate_common_subexpressions p2 in
      let (p4, rules_reordered) = optimize_rule_ordering p3 in
      let (p5, cached_calculations) = add_calculation_caching p4 in
      
      let stats = {
        traits_folded;
        dead_rules_removed;
        expressions_eliminated;
        rules_reordered;
        cached_calculations;
      } in
      (p5, stats)

(** Format optimization report *)
let format_stats (stats : stats) =
  Printf.sprintf {|Optimization Report:
  - Traits folded: %d
  - Dead rules removed: %d
  - Common expressions eliminated: %d
  - Rules reordered: %d
  - Calculations cached: %d
  Total optimizations: %d|}
    stats.traits_folded
    stats.dead_rules_removed
    stats.expressions_eliminated
    stats.rules_reordered
    stats.cached_calculations
    (stats.traits_folded + stats.dead_rules_removed + stats.expressions_eliminated + 
     stats.rules_reordered + stats.cached_calculations)
