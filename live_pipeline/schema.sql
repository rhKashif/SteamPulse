-- cleanup

DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS genre;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS developer;
DROP TABLE IF EXISTS publisher;
DROP TABLE IF EXISTS platform;

-- tables with no foreign key

CREATE TABLE developer(
    developer_id SMALLINT GENERATED ALWAYS AS IDENTITY,
    developer_name TEXT NOT NULL UNIQUE,
    PRIMARY KEY (developer_id)

);

CREATE TABLE publisher(
    publisher_id SMALLINT GENERATED ALWAYS AS IDENTITY,
    publisher_name TEXT NOT NULL UNIQUE,
    PRIMARY KEY (publisher_id)

);

CREATE TABLE platform(
    platform_id SMALLINT GENERATED ALWAYS AS IDENTITY,
    mac BOOLEAN NOT NULL,
    windows BOOLEAN NOT NULL,
    linux BOOLEAN NOT NULL,
    PRIMARY KEY (platform_id)

);

-- game references the three above tables

-- Leaving game_id as regular int - not likely to hit the smallint cap if we're just working with new games, 
-- but there are more games on steam than the smallint cap, so if this ran for years or we expanded to grab
-- all games, smallint would cause issues.

CREATE TABLE game(
    game_id INT GENERATED ALWAYS AS IDENTITY,
    app_id INT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    release_date DATE NOT NULL,
    price FLOAT NOT NULL,
    sale_price FLOAT NOT NULL,
    developer_id SMALLINT,
    publisher_id SMALLINT,
    platform_id SMALLINT,
    PRIMARY KEY (game_id),
    FOREIGN KEY (developer_id) REFERENCES developer(developer_id),
    FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id),
    FOREIGN KEY (platform_id) REFERENCES platform(platform_id)

);


-- review and genre reference game

-- default 0 might make sentiment analysis loading easier, but it's easy to take out if we don't use it

CREATE TABLE review(
    review_id INT GENERATED ALWAYS AS IDENTITY,
    sentiment FLOAT NOT NULL DEFAULT 0,
    review_text TEXT NOT NULL, 
    review_date DATE NOT NULL,
    game_id INT,
    PRIMARY KEY (review_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id) 

);


CREATE TABLE genre(
    genre_id SMALLINT GENERATED ALWAYS AS IDENTITY,
    genre TEXT NOT NULL,
    user_generated BOOLEAN NOT NULL,
    game_id INT,
    PRIMARY KEY (genre_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id)
);

-- Seeding 

INSERT INTO platform(mac, windows, linux)
VALUES 
    (TRUE, TRUE, TRUE),
    (FALSE, FALSE, FALSE),
    
    (TRUE, FALSE, FALSE),
    (FALSE, TRUE, FALSE),
    (FALSE, FALSE, TRUE),
    
    (FALSE, TRUE, TRUE),
    (TRUE, FALSE, TRUE),
    (TRUE, TRUE, FALSE);
    

-- Hard to seed games / devs / publishers / genre
-- although we could pick 5 very popular games to manually enter and test our review loading against