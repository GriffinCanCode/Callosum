open Base

(** Time units for trait modifiers *)
type time_unit = 
  | Day
  | Week  
  | Month
  | Year
  [@@deriving show, eq]

(** Context types for conditional trait application *)
type context = 
  | Topic of string
  | Situation of string
  | Time_of_day of string
  | Emotional_state of string
  [@@deriving show, eq]

(** Trait modifiers that change behavior over time or context *)
type trait_modifier = 
  | Decay of float * time_unit
  | When of context
  | Unless of context  
  | Amplifies of string * float
  | Transforms_to of string * float * int
  [@@deriving show, eq]

(** Core trait specification with strength and modifiers *)
type trait_spec = {
  name: string;
  strength: float;
  modifiers: trait_modifier list;
} [@@deriving show, eq]

(** Knowledge domain levels *)
type knowledge_level = 
  | Beginner 
  | Intermediate
  | Advanced
  | Expert
  [@@deriving show, eq]

(** Knowledge connections between domains *)
type knowledge_connection = {
  from_domain: string;
  to_domain: string; 
  strength: float;
  evolution_rate: float option;
} [@@deriving show, eq]

(** Knowledge domain specification *)
type knowledge_domain = {
  name: string;
  topics: (string * knowledge_level) list;
  connections: knowledge_connection list;
} [@@deriving show, eq]

(** Behavior condition *)
type behavior_condition = 
  | Tired
  | Motivated  
  | Context_match of string
  | Trait_above of string * float
  | Time_range of string * string
  [@@deriving show, eq]

(** Behavior action *)
type behavior_action = 
  | Prefer of string
  | Seek of string
  | Avoid of string  
  | Set_style of string * string
  [@@deriving show, eq]

(** Behavior rule linking conditions to actions *)
type behavior_rule = {
  condition: behavior_condition;
  action: behavior_action;
} [@@deriving show, eq]

(** Evolution trigger *)
type evolution_trigger = 
  | Learns of string
  | Time_in_domain of string * time_unit * int
  | Interaction_count of int
  | Feedback_score of float
  [@@deriving show, eq]

(** Evolution effect *)  
type evolution_effect = 
  | Trait_adjust of string * float
  | Unlock_domain of string
  | Add_connection of string * string * float
  | New_behavior of behavior_rule
  [@@deriving show, eq]

(** Evolution specification *)
type evolution_spec = {
  trigger: evolution_trigger;
  action: evolution_effect;
} [@@deriving show, eq]

(** Location information for error reporting *)
type location = {
  filename: string;
  start_line: int;
  start_col: int;
  end_line: int;
  end_col: int;
} [@@deriving show, eq]

(** Parse error with location *)
type parse_error = {
  message: string;
  location: location;
} [@@deriving show, eq]

(** Main personality definition *)
type personality = {
  name: string;
  traits: trait_spec list;
  knowledge: knowledge_domain list;
  behaviors: behavior_rule list;
  evolution: evolution_spec list;
} [@@deriving show, eq]
