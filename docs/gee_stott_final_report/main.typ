// IEEE Conference Paper Format
#set document(
  title: "Human-Chessbot: Training a Neural Network to Play Chess Like a Human",
  author: "Gee Stott",
)

// IEEE uses two-column format for conference papers
#set page(
  paper: "us-letter",
  margin: (
    top: 0.75in,
    bottom: 1in,
    left: 0.625in,
    right: 0.625in,
  ),
)

// Two-column layout with gutter
#show: columns.with(2, gutter: 0.25in)

// IEEE uses Times/serif font, 10pt for body text
#set text(
  font: ("Liberation Serif", "Noto Serif", "DejaVu Serif"),
  size: 10pt,
)

#set par(
  justify: true,
  leading: 0.65em,
  first-line-indent: 0.25in,
)

// Section numbering in IEEE format
#set heading(numbering: "I.A.1.")

// Configure heading styles
#show heading.where(level: 1): it => {
  set text(size: 10pt, weight: "bold")
  set align(center)
  smallcaps(it.body)
  v(0.5em)
}

#show heading.where(level: 2): it => {
  set text(size: 10pt, weight: "bold", style: "italic")
  it
  v(0.3em)
}

#show heading.where(level: 3): it => {
  set text(size: 10pt, weight: "bold", style: "italic")
  it
  v(0.3em)
}

// Title and author block (IEEE format)
#set align(center)
#text(size: 24pt, weight: "bold")[
  Human-Chessbot: Training a Neural Network \ to Play Chess Like a Human
]

#v(1em)

#text(size: 11pt)[
  Gee Stott\
  #text(size: 10pt, style: "italic")[
    // TODO: Add institution/affiliation
    // Department, University
  ]\
  #text(size: 10pt)[
    // TODO: Add email
    // email\@university.edu
  ]
]

#v(1.5em)
#set align(left)

// Abstract in IEEE format (single column at top)
#show <abstract>: it => {
  set par(first-line-indent: 0pt)
  text(weight: "bold", size: 9pt)[Abstract—]
  it.body
  v(1em)
}

#par(first-line-indent: 0pt)[
  #text(weight: "bold", size: 9pt)[Abstract—]
  #include "sections/abstract.typ"
]

#v(1em)

// Index terms (keywords)
#par(first-line-indent: 0pt)[
  #text(weight: "bold", style: "italic", size: 9pt)[Index Terms—]
  #text(size: 9pt)[Chess, Neural Networks, Machine Learning, Human-like AI, Deep Learning]
]

#v(1.5em)

// Main Sections
= Introduction
#include "sections/introduction.typ"

= Background and Related Work
#include "sections/background.typ"

= Methodology
#include "sections/methodology.typ"

= Implementation
#include "sections/implementation.typ"

= Results and Evaluation
#include "sections/results.typ"

= Discussion
#include "sections/discussion.typ"

= Conclusion and Future Work
#include "sections/conclusion.typ"

// References (IEEE format)
= References
#set par(first-line-indent: 0pt, hanging-indent: 0.25in)
#set text(size: 9pt)
#include "sections/references.typ"

// Appendices (if needed for IEEE conference papers)
#colbreak()
= Appendices
#include "sections/appendices.typ"
