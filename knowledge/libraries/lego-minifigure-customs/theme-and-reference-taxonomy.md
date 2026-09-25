# Themes, Characters, and Reference Taxonomy

Last researched: 2026-09-24

Themes are discovery facets, not identity. A figure may belong to several facets while resolving to one canonical character/source appearance.

## Primary theme families

official_lego_original; superheroes_comics; star_wars_space_opera; science_fiction; fantasy; historical; military; anime_manga; animation; film; television_streaming; video_games; horror_monsters; music; celebrity_real_people; sports; mythology_folklore; literature; tabletop; meme_novelty; creator_original; crossovers; other.

Recommended subthemes include DC, Marvel, Image/independent comics, Star Wars, Dragon Ball, One Piece and other anime/manga, Tolkien/Middle-earth, superhero animation, comic eras/continuities, game-specific skins, classic LEGO Castle/Space/Pirates/Adventurers, and historical periods such as ancient, medieval, early modern, Napoleonic, American Civil War, WWI, WWII, Cold War and modern.

Do not make franchise and medium the same field. Batman can be franchise=DC, medium=comic, continuity=New Earth and source_appearance=specific issue; another Batman can be medium=film with a specific film/costume.

## Character model

Character is the abstract identity.
Incarnation/Continuity distinguishes reboots, universes, adaptations or different people sharing a mantle.
SourceWork identifies the comic series/film/show/game/book/toy line.
SourceAppearance identifies the exact issue, episode, scene/frame, game outfit, illustration or other reference.
OutfitDesign groups repeated visual designs across appearances.
FigureRelease is the physical/custom product representing that design.

For named troopers/army builders, separate named individual from unit/role template. A 501st generic trooper and Captain Rex can share faction/armor-era tags without becoming one Character.

## Reference types

comic_cover, comic_panel, comic_issue, film_frame, film_costume, television_frame, animation_frame, game_model, game_skin, concept_art, promotional_art, official_character_sheet, packaging_art, trading_card, statue/collectible, action_figure/toy, official_merchandise, book_illustration, historical_photo, historical_uniform_reference, maker_render, seller_photo, collector_photo, fan_art, unknown.

ReferenceAsset must record creator/publisher when known, work/title, date/issue/episode/version, URL/source, image provenance/usage notes and confidence.

Maker renders and seller photos prove what a product was advertised to look like, not necessarily what canon source inspired it. Keep these relationships distinct.

## Appearance matching

Store evidence for costume markers such as emblem shape, mask/helmet geometry, cape/cloth configuration, belt, armor layout, colors, facial/hair treatment, weapon/prop, era-specific details and distinctive linework.

Allow match states: exact_confirmed, probable, broad_era_match, composite_design, maker_original_variation, source_unknown and conflicting_sources.

When the source is obscure, Agent OS should retain competing hypotheses until a primary/strong reference resolves them.

## Theme aliases and search

Store aliases separately from canonical tags: MCU, DCU/DCEU, CW, TCW, Legends, EU, DBZ, DBS, OP, LOTR and similar. Search aliases should resolve to canonical theme/continuity without replacing the original seller language.

Maker marketing names intentionally avoiding licensed character names should be stored as release_title plus resolved_character with evidence. Never replace the release title; both are useful for later search.
