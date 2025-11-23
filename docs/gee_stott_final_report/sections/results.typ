// Experiments section

== Dataset Description

We trained our model off of 823,000 games from January to May of 2013. These games were played by a wide breadth of players in a variety of states. The original maia model was split into 9 separate models split apart by elo ranges of 100 (e.g. 1100-1200) this limited the models generalizability and so we trained our model on one complete dataset to increase access. Exanding from 1100-1900 to 700-2500 to further increase access.

 #figure(
    image("../figures/elo-distribution.png"),
    caption: "Spread of the elos present in the training set."
)

One other key difference is the fact that both iterations of the maia paper are unable to play chess openings as they don't have any knowledge of the first 10 moves. This is a profound limitation as the opening is one of the key areas where players struggle within a game. So knowing this we choose to include the first 10 moves to increase the understanding of openings.

We also didn't limit the model to just the blitz games as we wanted to increase the overall variability in the games that the model was capable of representing. We introduced this noise as it gives a far more holistic view of human players. This was useful as blitz games only show up a small portion of the data and we want to show all human play.

#figure(
    image("../figures/time_control_distribution.png"),
    caption: "Time Control Splits of the games from Jan-May of 2013"
)

The Lichess dataset used in this project consists of over 1 billion chess games played on the Lichess.org platform between 2013-2023. Key characteristics:

- Total size: ~2TB of compressed game data
- Game format: Portable Game Notation (PGN)
- Rating range: 800-2900 ELO
- Game types: Classical, Rapid, Blitz, and Bullet time controls
- Key fields per game:
  * Player ELO ratings
  * Move sequences in UCI format
  * Game result
  * Time control
  * Opening classification
  * Timestamps

For training, we took data from January to May of 2013 consisting of 860,000 games from players rated 797-2412 ELO to focus on typical club-level play patterns. Games were validated to remove incomplete or corrupted entries.

Data processing pipeline:
1. PGN parsing and validation
2. Feature extraction (board states, moves, metadata)
3. Train/validation/test splitting (80/10/10)
4. Normalization of numerical features

== Baseline Description

All of the source code for this project is a available at https://github.com/EthanDGee/ryleeeeeeeeeeeee

== Experimental Evaluation
