// Appendices section

== Appendix A: Source Code Repository

All of the source code for this project is a available at https://github.com/EthanDGee/ryleeeeeeeeeeeee


== Appendix B: Dataset Details

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

== Appendix C: Additional Results

// TODO: Extended tables and figures
// TODO: Additional game examples
// TODO: Supplementary statistics
