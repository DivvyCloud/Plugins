--
-- Create a new table to store whitelisted image IDs within an installation
--
DROP TABLE IF EXISTS `ValidImages`;
CREATE TABLE `ValidImages` (
  `region_name` varchar(64) NOT NULL,
  `image_id` varchar(64) NOT NULL,
  PRIMARY KEY (`region_name`, `image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

