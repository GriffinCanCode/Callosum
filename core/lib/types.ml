open Base

(** Time units for AI personality trait evolution and decay *)
type time_unit = 
  | Day    (** Daily evolution cycles *)
  | Week   (** Weekly personality adjustments *)  
  | Month  (** Monthly long-term changes *)
  | Year   (** Yearly personality maturation *)
  [@@deriving show, eq]

(** Conversation context types for AI response adaptation *)
type context = 
  | Topic of string         (** Subject matter context (e.g., "teaching", "debugging") *)
  | Situation of string     (** Conversational situation (e.g., "user_frustrated", "celebration") *)
  | Time_of_day of string   (** Temporal context affecting AI mood *)
  | Emotional_state of string  (** User's emotional state for empathetic responses *)
  [@@deriving show, eq]

(** Dynamic trait modifiers for AI personality evolution *)
type trait_modifier = 
  | Decay of float * time_unit        (** Natural trait weakening over time *)
  | When of context                   (** Contextual trait activation *)
  | Unless of context                 (** Contextual trait suppression *)
  | Amplifies of string * float       (** Cross-trait amplification effects *)
  | Transforms_to of string * float * int  (** Long-term personality evolution *)
  [@@deriving show, eq]

(** Core AI personality trait with dynamic behavior *)
type trait_spec = {
  name: string;                    (** Trait identifier (e.g., "empathy", "curiosity") *)
  strength: float;                 (** Base strength 0.0-1.0 *)
  modifiers: trait_modifier list;  (** Dynamic behavior modifiers *)
} [@@deriving show, eq]

(** AI knowledge confidence and expertise levels *)
type knowledge_level = 
  | Beginner     (** Basic familiarity, may provide simple answers *)
  | Intermediate (** Solid understanding, can explain concepts *)
  | Advanced     (** Deep knowledge, can provide detailed insights *)
  | Expert       (** Comprehensive mastery, can teach and guide others *)
  [@@deriving show, eq]

(** Knowledge domain interconnections for AI reasoning *)
type knowledge_connection = {
  from_domain: string;           (** Source knowledge domain *)
  to_domain: string;             (** Connected knowledge domain *)
  strength: float;               (** Connection strength (0.0-1.0) *)
  evolution_rate: float option;  (** Rate of knowledge transfer *)
} [@@deriving show, eq]

(** AI knowledge domain with expertise mapping *)
type knowledge_domain = {
  name: string;                             (** Domain identifier (e.g., "conversation", "science") *)
  topics: (string * knowledge_level) list; (** Topic expertise levels *)
  connections: knowledge_connection list;   (** Inter-domain knowledge links *)
} [@@deriving show, eq]

(** Conversational behavior trigger conditions *)
type behavior_condition = 
  | Tired              (** AI experiencing processing fatigue *)
  | Motivated          (** AI in highly engaged state *)
  | Context_match of string    (** Specific conversation context detected *)
  | Trait_above of string * float  (** Trait threshold exceeded *)
  | Time_range of string * string  (** Time-based behavioral trigger *)
  [@@deriving show, eq]

(** AI response behavior and communication patterns *)
type behavior_action = 
  | Prefer of string           (** Favor certain response styles *)
  | Seek of string             (** Actively pursue conversation directions *)
  | Avoid of string            (** Avoid certain topics or approaches *)
  | Set_style of string * string  (** Adjust communication style *)
  [@@deriving show, eq]

(** Conditional behavior rule for AI responses *)
type behavior_rule = {
  condition: behavior_condition;  (** When this behavior should trigger *)
  action: behavior_action;        (** What the AI should do *)
} [@@deriving show, eq]

(** AI personality evolution triggers from interactions *)
type evolution_trigger = 
  | Learns of string                          (** Learning new information *)
  | Time_in_domain of string * time_unit * int  (** Extended focus in knowledge area *)
  | Interaction_count of int                  (** Number of user interactions *)
  | Feedback_score of float                   (** User satisfaction/feedback *)
  [@@deriving show, eq]

(** AI personality evolution effects and growth patterns *)  
type evolution_effect = 
  | Trait_adjust of string * float            (** Strengthen/weaken personality traits *)
  | Unlock_domain of string                   (** Gain access to new knowledge areas *)
  | Add_connection of string * string * float (** Form new knowledge connections *)
  | New_behavior of behavior_rule             (** Develop new behavioral patterns *)
  [@@deriving show, eq]

(** Complete evolution rule for AI personality growth *)
type evolution_spec = {
  trigger: evolution_trigger;  (** What causes the evolution *)
  action: evolution_effect;    (** How the personality changes *)
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

(** Complete AI language model personality definition *)
type personality = {
  name: string;                      (** Personality identifier and display name *)
  traits: trait_spec list;           (** Core personality traits with dynamic behavior *)
  knowledge: knowledge_domain list;  (** Knowledge domains and expertise levels *)
  behaviors: behavior_rule list;     (** Conversational behavior patterns *)
  evolution: evolution_spec list;    (** Rules for personality growth through interactions *)
} [@@deriving show, eq]
