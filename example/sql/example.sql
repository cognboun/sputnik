CREATE DATABASE `sputnik`;

CREATE TABLE `food_and_place` (
  `id` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `place_id` int(8) NOT NULL,
  `food_id` int(8) NOT NULL,
  `picture_count` int(4) NOT NULL DEFAULT '0',
  `comment_total` int(5) NOT NULL DEFAULT '0',
  `publish_time` datetime DEFAULT NULL,
  `best_picture_id` int(8) DEFAULT '0',
  `want_it_total` int(6) DEFAULT '0',
  `nom_it_total` int(6) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `food_and_place` (`food_id`,`place_id`),
  KEY `food_id` (`food_id`),
  KEY `place_id` (`place_id`),
  KEY `place_food` (`place_id`,`food_id`),
  KEY `best_picture_id` (`best_picture_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1008 DEFAULT CHARSET=utf8;
