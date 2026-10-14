#!/usr/bin/env ruby
# frozen_string_literal: true

require "cgi"

source_path = ARGV.fetch(0)
output_path = ARGV.fetch(1)

translations = {
  "A" => "Player presses Start / Next Scenario",
  "B" => "QuestManager",
  "C" => "Unity selects ScenarioDefinition",
  "D" => "Create NarrativeGenerationRequest",
  "E" => "Add previous completed story summary",
  "F" => "NarrativeApiClient sends HTTP POST",
  "G" => "Python Backend",
  "H" => "Validate Unity request",
  "I" => "Create System Prompt and User Prompt",
  "J" => "OpenAI Responses API",
  "K" => "Generate structured GeneratedNarrative",
  "L" => "Backend validates model output",
  "M" => "Return LLM narrative JSON",
  "N" => "Backend fixed fallback",
  "O" => "Unity NarrativeValidator validates again",
  "P" => "QuestManager starts scenario",
  "Q" => "Unity NarrativeTestProvider fallback",
  "R" => "ScenarioTargetResetter prepares targets",
  "S" => "QuestUI displays narrative and progress",
  "T" => "Player defeats enemies / boss / collects items",
  "U" => "Gameplay Event reports to QuestManager",
  "V" => "Update scenario progress",
  "W" => "CompleteScenario",
  "X" => "Display completionText",
  "Y" => "Grant fixed EXP / gold",
  "Z" => "Save storySummary to PlayerPrefs",
  "AA" => "Record scenario_completed event",
  "AB" => "Record generation JSONL",
  "AC" => "Record scenario_started JSONL",
  "AD" => "narrative_runs.jsonl",
  "AE" => "analyze_experiments.py",
  "AF" => "Statistical report and CSV"
}.freeze

svg = File.read(source_path)

# Mermaid places every node in a separate chunk beginning with this marker.
# Replacing only the first text element in each chunk preserves the original
# node positions, shapes, edges, arrows, and flow structure.
parts = svg.split(/(?=<g class="node )/)

parts.map! do |part|
  match = part.match(/id="[^"]*-flowchart-([A-Z]+)-\d+"/)
  next part unless match

  label = translations[match[1]]
  next part unless label

  escaped_label = CGI.escapeHTML(label)
  replacement = [
    '<tspan class="text-outer-tspan row" x="0" y="-0.1em" dy="1.1em">',
    '<tspan class="text-inner-tspan" font-style="normal">',
    escaped_label,
    '</tspan></tspan>'
  ].join

  part.sub(%r{(<text\b[^>]*>).*?(</text>)}m, "\\1#{replacement}\\2")
end

svg = parts.join

# Translate the three labelled decision/progress edges.
svg.gsub!(/>有效</, ">Valid<")
svg.gsub!(/>失敗</, ">Failed<")
svg.gsub!(/>達到數量</, ">Target reached<")

# English labels are wider than Chinese labels. A slightly smaller node font
# keeps the translated wording readable without changing the original layout.
style = <<~CSS.delete("\n")
  #mermaid-_r_ls_-1 .node .label{font-size:13px;letter-spacing:-0.1px;}
  #mermaid-_r_ls_-1 .edgeLabel{font-size:12px;}
CSS
svg.sub!("</style>", "#{style}</style>")

File.write(output_path, svg)
