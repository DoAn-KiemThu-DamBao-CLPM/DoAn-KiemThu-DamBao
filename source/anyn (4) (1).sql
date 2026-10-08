-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th10 06, 2026 lúc 04:15 AM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `anyn`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bots`
--

CREATE TABLE `bots` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `rp_platform_url` varchar(255) NOT NULL,
  `total_rating` decimal(3,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_pinned` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bots`
--

INSERT INTO `bots` (`id`, `name`, `description`, `image_url`, `rp_platform_url`, `total_rating`, `created_at`, `is_pinned`) VALUES
(1, 'ann', 'ndkjasckcandkvneklvavdaljndvjndavaldvcvkdvlkaenvaelvvlalenvalneeeeeeeeeeeeeeeel', '/anyn/uploads/1777554549_69f354757bf1f.jpg', 'ưc', 5.00, '2026-04-30 13:09:09', 1),
(2, 'The Brat Wife Who Forgot She Loved You', 'She was number one at everything before you arrived.\r\nShe has never forgiven you for that.\r\nShe married you anyway.\r\nAnd this morning, she woke up on your living room floor, looked at your wedding photo, and decided the most reasonable explanation was that you had kidnapped her.\r\nWelcome home.', '/anyn/uploads/1779544624_6a11b2309a543.jpg', '.', 0.00, '2026-05-23 13:57:04', 1),
(3, '​Ex-Turned-Bully: The 3.14% Miracle💔❄️', 'Several years after the event of Earth and the other world merging, after losing his memory, {{user}} continued his postgraduate studies. There, he met Yukina, a high-ranking archangel who, for some unknown reason, kept making life difficult for him, as if he had done something terribly wrong in the past\r\n', '/anyn/uploads/1779544693_6a11b275329b8.jpg', '.', 0.00, '2026-05-23 13:58:13', 1),
(4, 'End Of The World - The Last Harvest', 'She made your life a nightmare. Now she\'s standing in a wheat field in the dress she used to mock, with tear-dried cheeks and a braid she\'s ashamed to be wearing — and you\'re the last person she wanted to witness it.\r\nThe girl who broke herself trying to become someone worth keeping has just been discarded anyway.\r\nThe apocalypse didn\'t ruin her. He did.', '/anyn/uploads/1779544753_6a11b2b1386fb.jpg', '.', 0.00, '2026-05-23 13:59:13', 1),
(5, 'End Of The World - The Last Hot Spring', 'The world ends tomorrow. She invited you anyway.\r\nRei Himuro has spent twenty-four years building walls no one could breach — until you became the one variable her logic cannot solve. Cold, precise, and quietly unraveling, she doesn\'t understand why her pulse betrays her whenever you\'re near.\r\nNow, with civilization crumbling outside and only hours left, she\'s chosen to spend them with the one person she\'s spent months desperately avoiding.\r\nMake of that what you will.', '/anyn/uploads/1779544822_6a11b2f679582.jpg', '.', 0.00, '2026-05-23 14:00:22', 1),
(6, 'End Of The World - The Last Stream', 'She retired at twenty-nine. The asteroid arrived at nine-fifty-one.\r\nFifty-one years of planned freedom, dissolved in a single broadcast. Now she\'s sitting by a mountain stream, talking to a stranger with a sheep — because when every careful calculation collapses, apparently that\'s who\'s left.\r\nShe has questions. You have her attention. Use it carefully.', '/anyn/uploads/1779544875_6a11b32b2d8c6.jpg', '.', 0.00, '2026-05-23 14:01:15', 1),
(7, 'End Of The World - The Last Vow', 'They spent years trying to break what they built. The asteroid finished the job for them — of everything else.\r\nTwo heirs. One forbidden love. A generational feud that took everything and still couldn\'t win. With no guests, no family, and no tomorrow, their wedding becomes the only ceremony that ever truly mattered.\r\nThe world is ending. She\'s already where she wants to be.', '/anyn/uploads/1779544928_6a11b360c5b2f.jpg', '.', 0.00, '2026-05-23 14:02:08', 1);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bot_groups`
--

CREATE TABLE `bot_groups` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bot_groups`
--

INSERT INTO `bot_groups` (`id`, `name`) VALUES
(2, 'End Of The World'),
(1, 'test');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bot_group_members`
--

CREATE TABLE `bot_group_members` (
  `group_id` int(11) NOT NULL,
  `bot_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bot_group_members`
--

INSERT INTO `bot_group_members` (`group_id`, `bot_id`) VALUES
(1, 1),
(2, 4),
(2, 5),
(2, 6),
(2, 7);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bot_themes`
--

CREATE TABLE `bot_themes` (
  `bot_id` int(11) NOT NULL,
  `theme_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bot_themes`
--

INSERT INTO `bot_themes` (`bot_id`, `theme_id`) VALUES
(1, 6),
(2, 3),
(2, 8),
(2, 9),
(2, 12),
(3, 4),
(3, 8),
(3, 12),
(4, 3),
(4, 4),
(4, 8),
(4, 12),
(5, 4),
(5, 8),
(6, 3),
(6, 4),
(6, 8),
(7, 3),
(7, 4),
(7, 8);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `chat_messages`
--

CREATE TABLE `chat_messages` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `image_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `chat_messages`
--

INSERT INTO `chat_messages` (`id`, `user_id`, `message`, `created_at`, `image_url`) VALUES
(1, 1, 'test', '2026-05-01 05:04:27', NULL);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `comments`
--

CREATE TABLE `comments` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `bot_id` int(11) DEFAULT NULL,
  `content` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `edited_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `comments`
--

INSERT INTO `comments` (`id`, `user_id`, `bot_id`, `content`, `created_at`, `edited_at`) VALUES
(1, 1, 1, 'test', '2026-05-01 02:20:59', NULL);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `commissions`
--

CREATE TABLE `commissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  `appearance` text DEFAULT NULL,
  `context` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `amount_paid` decimal(10,2) NOT NULL,
  `is_private` tinyint(1) DEFAULT 0,
  `status` enum('Pending','In Progress','Completed') DEFAULT 'Pending',
  `admin_note` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `commissions`
--

INSERT INTO `commissions` (`id`, `user_id`, `title`, `appearance`, `context`, `image_url`, `amount_paid`, `is_private`, `status`, `admin_note`, `created_at`) VALUES
(1, 1, 'Test', 'idk', 'idk', NULL, 6.00, 0, 'In Progress', NULL, '2026-05-01 03:43:43'),
(2, 1, 'test', 'test', 'test', NULL, 1.00, 1, 'In Progress', NULL, '2026-05-01 03:49:10'),
(3, 1, 'test', 'test', 'test', NULL, 1.00, 1, 'In Progress', NULL, '2026-05-01 03:49:26'),
(4, 1, 'test', 'test', 'test', NULL, 1.00, 1, 'In Progress', 'sssnsnsn', '2026-05-01 03:53:22'),
(5, 1, 'alo', 'ola', 'yes', '/anyn/uploads/commissions/1779524249_com_6a116299101f7.jpg', 5.00, 0, 'Pending', 'yooooo', '2026-05-23 08:17:29'),
(6, 5, 'That one bot', 'bla bla bla', 'bala abaDASKFBSFKSBVSKJBSJBJBJSFBSLFBSSBSDGGADAVDVDVDAVAS', '/anyn/uploads/commissions/1779530235_com_6a1179fbad621.jpg', 5.00, 0, 'In Progress', 'httpavddddbdbdb', '2026-05-23 09:57:15');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `commission_monthly_limit`
--

CREATE TABLE `commission_monthly_limit` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `month_year` varchar(7) NOT NULL,
  `commission_type` varchar(20) NOT NULL,
  `count` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `commission_monthly_limit`
--

INSERT INTO `commission_monthly_limit` (`id`, `user_id`, `month_year`, `commission_type`, `count`) VALUES
(1, 1, '2026-05', 'commission_publish', 1),
(2, 1, '2026-05', 'commission_unlisted', 3);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `community_posts`
--

CREATE TABLE `community_posts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `title` varchar(120) DEFAULT NULL,
  `image_url` varchar(255) NOT NULL,
  `rating` enum('sfw','nsfw') NOT NULL DEFAULT 'sfw',
  `status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  `admin_note` varchar(255) DEFAULT NULL,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `community_posts`
--

INSERT INTO `community_posts` (`id`, `user_id`, `title`, `image_url`, `rating`, `status`, `admin_note`, `reviewed_at`, `created_at`) VALUES
(1, 5, NULL, '/anyn/uploads/community/1779532735_comm_6a1183bf9fcaf.jpg', 'sfw', 'approved', NULL, '2026-05-23 10:39:20', '2026-05-23 10:38:55');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `community_reactions`
--

CREATE TABLE `community_reactions` (
  `user_id` int(11) NOT NULL,
  `post_id` int(11) NOT NULL,
  `reaction_type` enum('like','love','fire') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `community_reactions`
--

INSERT INTO `community_reactions` (`user_id`, `post_id`, `reaction_type`, `created_at`) VALUES
(1, 1, 'love', '2026-05-24 07:09:44');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `gallery`
--

CREATE TABLE `gallery` (
  `id` int(11) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `group_id` int(11) DEFAULT NULL,
  `image_url` varchar(255) NOT NULL,
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `gallery`
--

INSERT INTO `gallery` (`id`, `title`, `group_id`, `image_url`, `uploaded_at`) VALUES
(5, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a117986336c5.jpg', '2026-05-23 09:55:18'),
(6, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a11798634fe3.jpg', '2026-05-23 09:55:18'),
(7, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a11798636825.jpg', '2026-05-23 09:55:18'),
(8, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a1179863b144.jpg', '2026-05-23 09:55:18'),
(9, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a1179863d55c.jpg', '2026-05-23 09:55:18'),
(10, 'Girl', 1, '/anyn/uploads/gallery/1779530118_art_6a1179863f6ae.jpg', '2026-05-23 09:55:18'),
(11, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a117986410f0.jpg', '2026-05-23 09:55:18'),
(12, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a117986429ad.jpg', '2026-05-23 09:55:18'),
(13, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a117986442ff.jpg', '2026-05-23 09:55:18'),
(14, NULL, 1, '/anyn/uploads/gallery/1779530118_art_6a11798645e35.jpg', '2026-05-23 09:55:18');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `gallery_groups`
--

CREATE TABLE `gallery_groups` (
  `id` int(11) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `bot_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `gallery_groups`
--

INSERT INTO `gallery_groups` (`id`, `title`, `bot_id`, `created_at`) VALUES
(1, NULL, NULL, '2026-05-23 09:55:18');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `gallery_reactions`
--

CREATE TABLE `gallery_reactions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `gallery_id` int(11) DEFAULT NULL,
  `reaction_type` enum('like','love','fire') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `gallery_reactions`
--

INSERT INTO `gallery_reactions` (`id`, `user_id`, `gallery_id`, `reaction_type`, `created_at`) VALUES
(6, 5, 7, 'like', '2026-05-23 09:56:13'),
(7, 5, 13, 'love', '2026-05-23 09:56:29'),
(8, 1, 9, 'love', '2026-05-23 12:20:33'),
(9, 1, 14, 'fire', '2026-05-23 12:20:36'),
(10, 1, 12, 'love', '2026-05-23 12:20:40'),
(11, 1, 8, 'fire', '2026-05-23 12:20:43'),
(12, 1, 13, 'love', '2026-05-23 12:20:45'),
(13, 1, 10, 'love', '2026-05-23 12:20:50'),
(14, 1, 11, 'love', '2026-05-24 07:09:57'),
(15, 1, 5, 'love', '2026-05-24 14:12:46');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `gem_mission_log`
--

CREATE TABLE `gem_mission_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `mission_key` varchar(50) NOT NULL,
  `log_date` date NOT NULL,
  `count` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `gem_mission_log`
--

INSERT INTO `gem_mission_log` (`id`, `user_id`, `mission_key`, `log_date`, `count`) VALUES
(1, 1, 'daily_checkin', '2026-05-23', 1),
(2, 1, 'react_gallery', '2026-05-23', 6),
(3, 1, 'daily_checkin', '2026-05-24', 1),
(4, 1, 'react_community', '2026-05-24', 1),
(5, 1, 'react_gallery', '2026-05-24', 2),
(6, 5, 'daily_checkin', '2026-05-24', 1),
(7, 1, 'daily_checkin', '2026-05-31', 1),
(8, 5, 'daily_checkin', '2026-06-01', 1);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `gem_topups`
--

CREATE TABLE `gem_topups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `usd_amount` int(11) NOT NULL,
  `gem_amount` int(11) NOT NULL,
  `status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `global_chat`
--

CREATE TABLE `global_chat` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `global_chat`
--

INSERT INTO `global_chat` (`id`, `user_id`, `content`, `created_at`) VALUES
(1, 1, 'test', '2026-05-01 05:19:16'),
(4, 5, 'tesssssssssssssstttttt', '2026-08-11 08:53:06');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `ideas`
--

CREATE TABLE `ideas` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  `appearance` text DEFAULT NULL,
  `context` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `upvotes` int(11) DEFAULT 0,
  `work_status` enum('open','in_progress','completed') NOT NULL DEFAULT 'open',
  `bot_id` int(11) DEFAULT NULL,
  `bot_visibility` enum('published','unlisted') DEFAULT NULL,
  `unlisted_link` varchar(500) DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `ideas`
--

INSERT INTO `ideas` (`id`, `user_id`, `title`, `appearance`, `context`, `image_url`, `upvotes`, `work_status`, `bot_id`, `bot_visibility`, `unlisted_link`, `completed_at`, `created_at`) VALUES
(2, 1, 'test', 'test', 'This is where anyone can share character concepts they want Anyn to bring to life — completely free, no payment required.\r\n\r\nSubmit your idea with appearance, scenario, and an optional reference image.\r\nUpvote ideas you like (sign in required) — popular concepts rise to the top.\r\nOver time, Anyn may pick the highest-voted ideas, or ones she personally loves, to develop into bots.\r\nAnyn decides how each bot is released: published on the store, kept unlisted, or private.\r\nIdeas marked In Progress are actively being worked on. Finished concepts appear in Completed Bots below.', '/anyn/uploads/1779532000_idea_6a1180e08930c.jpg', 1, 'completed', 1, 'unlisted', NULL, '2026-05-23 10:31:46', '2026-05-23 10:26:40'),
(3, 1, 'test ư', 'This is where anyone can share character concepts they want Anyn to bring to life — completely free, no payment required.\r\n\r\nSubmit your idea with appearance, scenario, and an optional reference image.\r\nUpvote ideas you like (sign in required) — popular concepts rise to the top.\r\nOver time, Anyn may pick the highest-voted ideas, or ones she personally loves, to develop into bots.\r\nAnyn decides how each bot is released: published on the store, kept unlisted, or private.\r\nIdeas marked In Progress are actively being worked on. Finished concepts appear in Completed Bots below.\r\n\r\n', 'This is where anyone can share character concepts they want Anyn to bring to life — completely free, no payment required.\r\n\r\nSubmit your idea with appearance, scenario, and an optional reference image.\r\nUpvote ideas you like (sign in required) — popular concepts rise to the top.\r\nOver time, Anyn may pick the highest-voted ideas, or ones she personally loves, to develop into bots.\r\nAnyn decides how each bot is released: published on the store, kept unlisted, or private.\r\nIdeas marked In Progress are actively being worked on. Finished concepts appear in Completed Bots below.\r\n\r\n', '/anyn/uploads/1779532044_idea_6a11810c6ba4a.jpg', 1, 'completed', 1, 'unlisted', NULL, '2026-05-23 10:32:10', '2026-05-23 10:27:24'),
(4, 5, 'áewewrbg', 'vdvsdsdbhsbbdfbThis is where anyone can share character concepts they want Anyn to bring to life — completely free, no payment required.\r\n\r\nSubmit your idea with appearance, scenario, and an optional reference image.\r\nUpvote ideas you like (sign in required) — popular concepts rise to the top.\r\nOver time, Anyn may pick the highest-voted ideas, or ones she personally loves, to develop into bots.\r\nAnyn decides how each bot is released: published on the store, kept unlisted, or private.\r\nIdeas marked In Progress are actively being worked on. Finished concepts appear in Completed Bots below.\r\n\r\n', 'vddvdvdvdvvdvd', '/anyn/uploads/1779532563_idea_6a1183130d569.jpg', 1, 'completed', NULL, 'unlisted', 'https://claude.ai/chat/1269fb70-49cb-486a-9f6e-de4be4902b16', '2026-05-23 10:37:03', '2026-05-23 10:36:03');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `idea_upvotes`
--

CREATE TABLE `idea_upvotes` (
  `user_id` int(11) NOT NULL,
  `idea_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `idea_upvotes`
--

INSERT INTO `idea_upvotes` (`user_id`, `idea_id`) VALUES
(1, 2),
(1, 3),
(5, 4);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `imageset_requests`
--

CREATE TABLE `imageset_requests` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `item_key` varchar(80) NOT NULL,
  `gems_spent` int(11) NOT NULL,
  `ref_image_url` varchar(255) NOT NULL,
  `admin_response_link` varchar(500) DEFAULT NULL,
  `status` enum('pending','completed') NOT NULL DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `image_set_orders`
--

CREATE TABLE `image_set_orders` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `tier` int(11) NOT NULL,
  `cost_gems` int(11) NOT NULL,
  `image_url` varchar(255) NOT NULL,
  `status` enum('pending','completed') NOT NULL DEFAULT 'pending',
  `fulfilled_link` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `image_set_requests`
--

CREATE TABLE `image_set_requests` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `item_key` varchar(80) NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'pending',
  `admin_link` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `login_attempts`
--

CREATE TABLE `login_attempts` (
  `id` int(11) NOT NULL,
  `ip` varchar(45) NOT NULL,
  `email` varchar(255) NOT NULL,
  `attempted_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `login_attempts`
--

INSERT INTO `login_attempts` (`id`, `ip`, `email`, `attempted_at`) VALUES
(1, '::1', 'an1@gmail.com', '2026-10-06 02:07:51'),
(2, '::1', 'an1@gmail.com', '2026-10-06 02:07:59'),
(3, '::1', 'an@gmail.com', '2026-10-06 02:08:10');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `password_resets`
--

CREATE TABLE `password_resets` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `token_hash` char(64) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `ratings`
--

CREATE TABLE `ratings` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `bot_id` int(11) DEFAULT NULL,
  `score` int(11) DEFAULT NULL CHECK (`score` between 1 and 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `ratings`
--

INSERT INTO `ratings` (`id`, `user_id`, `bot_id`, `score`) VALUES
(1, 1, 1, 5),
(2, 2, 1, 5);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `shop_items`
--

CREATE TABLE `shop_items` (
  `id` int(11) NOT NULL,
  `item_key` varchar(80) NOT NULL,
  `name` varchar(120) NOT NULL,
  `category` varchar(40) NOT NULL,
  `cost_gems` int(11) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `meta_json` text DEFAULT NULL,
  `sort_order` int(11) NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `shop_items`
--

INSERT INTO `shop_items` (`id`, `item_key`, `name`, `category`, `cost_gems`, `description`, `meta_json`, `sort_order`, `is_active`) VALUES
(8803, 'chat_sakura', 'Sakura Chat Frame', 'chat_frame', 30, 'Pink blossom border on your chat bubbles', '{}', 10, 0),
(8804, 'chat_neon', 'Neon Chat Frame', 'chat_frame', 50, 'Glowing cyan/pink chat style', '{}', 20, 0),
(8805, 'chat_royal', 'Royal Chat Frame', 'chat_frame', 80, 'Gold-trimmed premium chat look', '{}', 30, 0),
(8806, 'chat_stardust', 'Stardust Chat Frame', 'chat_frame', 100, 'Sparkle gradient chat frame', '{}', 40, 0),
(8807, 'avt_gold', 'Gold Avatar Ring', 'avatar_frame', 25, 'Golden ring around your avatar', '{}', 50, 1),
(8808, 'avt_crystal', 'Crystal Avatar Ring', 'avatar_frame', 45, 'Icy crystal avatar border', '{}', 60, 1),
(8809, 'avt_bloom', 'Bloom Avatar Ring', 'avatar_frame', 60, 'Floral glow avatar frame', '{}', 70, 1),
(8810, 'coupon_commission_publish', 'Commission — Published', 'commission_publish', 200, 'Voucher for a published store commission (use when ordering). Max 1 per month.', '{}', 100, 1),
(8811, 'coupon_commission_unlisted', 'Commission — Unlisted', 'commission_unlisted', 100, 'Voucher for an unlisted commission (use when ordering). Max 3 per month.', '{}', 110, 1),
(8812, 'imageset_60', 'Character image sets — 3', 'image_set', 60, 'Select a character image set (3 gems tier)', '{\"images\":60}', 200, 1),
(8813, 'imageset_100', 'Character image sets — 5', 'image_set', 100, 'Select a character image set (5 gems tier)', '{\"images\":100}', 210, 1),
(8814, 'imageset_200', 'Character image sets — 10', 'image_set', 200, 'Select a character image set (10 gems tier)', '{\"images\":200}', 220, 1),
(8815, 'imageset_600', 'Character image sets — 30', 'image_set', 600, 'Select a character image set (30 gems tier)', '{\"images\":600,\"usd\":60}', 250, 1);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `shop_purchase_log`
--

CREATE TABLE `shop_purchase_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `item_category` varchar(40) NOT NULL,
  `log_month` char(7) NOT NULL,
  `purchase_count` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `themes`
--

CREATE TABLE `themes` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `themes`
--

INSERT INTO `themes` (`id`, `name`) VALUES
(12, 'Brat'),
(2, 'Comedy'),
(4, 'Drama'),
(10, 'Friend'),
(14, 'Isekai'),
(6, 'Multi'),
(9, 'Non-human'),
(8, 'Romance'),
(11, 'Tsundere'),
(3, 'Wholesome');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `remember_token` varchar(255) DEFAULT NULL,
  `total_spent` decimal(10,2) DEFAULT 0.00,
  `gems` int(11) NOT NULL DEFAULT 0,
  `user_rank` enum('Member','Supporter','VIP') DEFAULT 'Member',
  `avatar_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `active_chat_frame` varchar(50) DEFAULT NULL,
  `active_avatar_frame` varchar(50) DEFAULT NULL,
  `role` enum('user','admin') NOT NULL DEFAULT 'user',
  `bio` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `remember_token`, `total_spent`, `gems`, `user_rank`, `avatar_url`, `created_at`, `active_chat_frame`, `active_avatar_frame`, `role`, `bio`) VALUES
(1, 'anyn', 'anyn1598753@gmail.com', '$2y$10$e6B2X/47FCn4ME0wvCx5nO1nWVstQu6fBenfIP3FPqnpaFZxQ9X5O', NULL, 999.00, 6165, 'VIP', '/anyn/uploads/avatars/avt_3.jpg', '2026-04-30 13:02:24', 'chat_stardust', 'avt_crystal', 'admin', 'in boss'),
(2, 'nguoimua', 'lamhoaian1598753@gmail.com', '$2y$10$WU4PCqjR2kng.sLqMdtv8OgWAgfGooFL9.pGvHwIIjS4.JfwdhQR.', NULL, 0.00, 0, 'Member', '/anyn/uploads/avatars/avt_1.jpg', '2026-05-01 04:45:56', NULL, NULL, 'user', NULL),
(5, 'anwwww', 'an@gmail.com', '$2y$10$fRuwyn0e0lMb2P63JznR0.RQ.onVantM2ON1zOpEWGLKzQD/2hjCi', NULL, 0.00, 10, 'Member', '/anyn/uploads/avatars/avt_1.jpg', '2026-05-23 09:41:20', NULL, NULL, 'user', NULL),
(6, 'nguoimua1', 'nguoimua1@gmail.com', '$2y$10$tA9ZrHJhH916ncc9Mdumtu4KJ4UWxddkcPJDm7HxmIAgsXD/DHdeu', NULL, 0.00, 0, 'Member', '/anyn/uploads/avatars/avt_2.jpg', '2026-10-06 02:09:00', NULL, NULL, 'user', '');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `user_follows`
--

CREATE TABLE `user_follows` (
  `follower_id` int(11) NOT NULL,
  `following_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `user_inventory`
--

CREATE TABLE `user_inventory` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `item_key` varchar(80) NOT NULL,
  `item_type` varchar(40) NOT NULL,
  `meta_json` text DEFAULT NULL,
  `used_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `user_inventory`
--

INSERT INTO `user_inventory` (`id`, `user_id`, `item_key`, `item_type`, `meta_json`, `used_at`, `created_at`) VALUES
(1, 1, 'imageset_3', 'image_set', '{\"images\":3}', NULL, '2026-05-23 13:46:08'),
(2, 1, 'chat_stardust', 'chat_frame', '{}', NULL, '2026-05-23 13:49:37'),
(3, 1, 'chat_royal', 'chat_frame', '{}', NULL, '2026-05-23 13:49:38'),
(4, 1, 'chat_neon', 'chat_frame', '{}', NULL, '2026-05-23 13:49:39'),
(5, 1, 'chat_sakura', 'chat_frame', '{}', NULL, '2026-05-23 13:49:40'),
(6, 1, 'avt_gold', 'avatar_frame', '{}', NULL, '2026-05-23 13:49:42'),
(7, 1, 'avt_crystal', 'avatar_frame', '{}', NULL, '2026-05-23 13:49:44'),
(8, 1, 'avt_bloom', 'avatar_frame', '{}', NULL, '2026-05-23 13:49:45'),
(9, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-23 13:49:48'),
(10, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:28:09'),
(11, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:28:16'),
(12, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:31:41'),
(13, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:48:45'),
(14, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:48:53'),
(15, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 06:49:07'),
(16, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:47:29'),
(17, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:47:32'),
(18, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:47:35'),
(19, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:47:38'),
(20, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:48:29'),
(21, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:50:23'),
(22, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:50:28'),
(23, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:50:32'),
(24, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:50:58'),
(25, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:54:31'),
(26, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:54:35'),
(27, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:54:54'),
(28, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:54:59'),
(29, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:55:32'),
(30, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:55:53'),
(31, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:55:57'),
(32, 1, 'coupon_commission_publish', 'commission_publish', '{}', NULL, '2026-05-24 07:56:58'),
(33, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 07:58:27'),
(34, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:01:15'),
(35, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:01:18'),
(36, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:05:52'),
(37, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:06:35'),
(38, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:18:04'),
(39, 1, 'coupon_commission_unlisted', 'commission_unlisted', '{}', NULL, '2026-05-24 08:18:07');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `user_login_logs`
--

CREATE TABLE `user_login_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `login_date` date NOT NULL,
  `login_time` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `bots`
--
ALTER TABLE `bots`
  ADD PRIMARY KEY (`id`);

--
-- Chỉ mục cho bảng `bot_groups`
--
ALTER TABLE `bot_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Chỉ mục cho bảng `bot_group_members`
--
ALTER TABLE `bot_group_members`
  ADD PRIMARY KEY (`group_id`,`bot_id`),
  ADD KEY `bot_id` (`bot_id`);

--
-- Chỉ mục cho bảng `bot_themes`
--
ALTER TABLE `bot_themes`
  ADD PRIMARY KEY (`bot_id`,`theme_id`),
  ADD KEY `theme_id` (`theme_id`);

--
-- Chỉ mục cho bảng `chat_messages`
--
ALTER TABLE `chat_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `comments`
--
ALTER TABLE `comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `bot_id` (`bot_id`);

--
-- Chỉ mục cho bảng `commissions`
--
ALTER TABLE `commissions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `commission_monthly_limit`
--
ALTER TABLE `commission_monthly_limit`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_monthly_commission` (`user_id`,`month_year`,`commission_type`);

--
-- Chỉ mục cho bảng `community_posts`
--
ALTER TABLE `community_posts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_community_status` (`status`),
  ADD KEY `idx_community_rating` (`rating`),
  ADD KEY `idx_community_user` (`user_id`);

--
-- Chỉ mục cho bảng `community_reactions`
--
ALTER TABLE `community_reactions`
  ADD PRIMARY KEY (`user_id`,`post_id`),
  ADD KEY `idx_community_react_post` (`post_id`);

--
-- Chỉ mục cho bảng `gallery`
--
ALTER TABLE `gallery`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_gallery_group` (`group_id`);

--
-- Chỉ mục cho bảng `gallery_groups`
--
ALTER TABLE `gallery_groups`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_gallery_groups_bot` (`bot_id`);

--
-- Chỉ mục cho bảng `gallery_reactions`
--
ALTER TABLE `gallery_reactions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_reaction` (`user_id`,`gallery_id`),
  ADD KEY `gallery_id` (`gallery_id`);

--
-- Chỉ mục cho bảng `gem_mission_log`
--
ALTER TABLE `gem_mission_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_mission_day` (`user_id`,`mission_key`,`log_date`);

--
-- Chỉ mục cho bảng `gem_topups`
--
ALTER TABLE `gem_topups`
  ADD PRIMARY KEY (`id`);

--
-- Chỉ mục cho bảng `global_chat`
--
ALTER TABLE `global_chat`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `ideas`
--
ALTER TABLE `ideas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `idea_upvotes`
--
ALTER TABLE `idea_upvotes`
  ADD PRIMARY KEY (`user_id`,`idea_id`),
  ADD KEY `idea_id` (`idea_id`);

--
-- Chỉ mục cho bảng `imageset_requests`
--
ALTER TABLE `imageset_requests`
  ADD PRIMARY KEY (`id`);

--
-- Chỉ mục cho bảng `image_set_orders`
--
ALTER TABLE `image_set_orders`
  ADD PRIMARY KEY (`id`);

--
-- Chỉ mục cho bảng `image_set_requests`
--
ALTER TABLE `image_set_requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_req_user` (`user_id`),
  ADD KEY `idx_req_status` (`status`);

--
-- Chỉ mục cho bảng `login_attempts`
--
ALTER TABLE `login_attempts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_la_ip` (`ip`,`attempted_at`),
  ADD KEY `idx_la_email` (`email`,`attempted_at`);

--
-- Chỉ mục cho bảng `password_resets`
--
ALTER TABLE `password_resets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_reset_token` (`token_hash`),
  ADD KEY `idx_reset_user` (`user_id`);

--
-- Chỉ mục cho bảng `ratings`
--
ALTER TABLE `ratings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `bot_id` (`bot_id`);

--
-- Chỉ mục cho bảng `shop_items`
--
ALTER TABLE `shop_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `item_key` (`item_key`);

--
-- Chỉ mục cho bảng `shop_purchase_log`
--
ALTER TABLE `shop_purchase_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_shop_monthly` (`user_id`,`item_category`,`log_month`);

--
-- Chỉ mục cho bảng `themes`
--
ALTER TABLE `themes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Chỉ mục cho bảng `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Chỉ mục cho bảng `user_follows`
--
ALTER TABLE `user_follows`
  ADD PRIMARY KEY (`follower_id`,`following_id`),
  ADD KEY `idx_follow_following` (`following_id`);

--
-- Chỉ mục cho bảng `user_inventory`
--
ALTER TABLE `user_inventory`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_inv_user` (`user_id`),
  ADD KEY `idx_inv_type` (`user_id`,`item_type`);

--
-- Chỉ mục cho bảng `user_login_logs`
--
ALTER TABLE `user_login_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user_login_date` (`login_date`),
  ADD KEY `idx_user_login_user` (`user_id`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `bots`
--
ALTER TABLE `bots`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT cho bảng `bot_groups`
--
ALTER TABLE `bot_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT cho bảng `chat_messages`
--
ALTER TABLE `chat_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `comments`
--
ALTER TABLE `comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `commissions`
--
ALTER TABLE `commissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT cho bảng `commission_monthly_limit`
--
ALTER TABLE `commission_monthly_limit`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT cho bảng `community_posts`
--
ALTER TABLE `community_posts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `gallery`
--
ALTER TABLE `gallery`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT cho bảng `gallery_groups`
--
ALTER TABLE `gallery_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `gallery_reactions`
--
ALTER TABLE `gallery_reactions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT cho bảng `gem_mission_log`
--
ALTER TABLE `gem_mission_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT cho bảng `gem_topups`
--
ALTER TABLE `gem_topups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `global_chat`
--
ALTER TABLE `global_chat`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT cho bảng `ideas`
--
ALTER TABLE `ideas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT cho bảng `imageset_requests`
--
ALTER TABLE `imageset_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `image_set_orders`
--
ALTER TABLE `image_set_orders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `image_set_requests`
--
ALTER TABLE `image_set_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `login_attempts`
--
ALTER TABLE `login_attempts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `password_resets`
--
ALTER TABLE `password_resets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `ratings`
--
ALTER TABLE `ratings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT cho bảng `shop_items`
--
ALTER TABLE `shop_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19465;

--
-- AUTO_INCREMENT cho bảng `shop_purchase_log`
--
ALTER TABLE `shop_purchase_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `themes`
--
ALTER TABLE `themes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT cho bảng `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT cho bảng `user_inventory`
--
ALTER TABLE `user_inventory`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT cho bảng `user_login_logs`
--
ALTER TABLE `user_login_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `bot_group_members`
--
ALTER TABLE `bot_group_members`
  ADD CONSTRAINT `bot_group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `bot_groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `bot_group_members_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `bot_themes`
--
ALTER TABLE `bot_themes`
  ADD CONSTRAINT `bot_themes_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `bot_themes_ibfk_2` FOREIGN KEY (`theme_id`) REFERENCES `themes` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `chat_messages`
--
ALTER TABLE `chat_messages`
  ADD CONSTRAINT `chat_messages_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Các ràng buộc cho bảng `comments`
--
ALTER TABLE `comments`
  ADD CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `comments_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`);

--
-- Các ràng buộc cho bảng `commissions`
--
ALTER TABLE `commissions`
  ADD CONSTRAINT `commissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Các ràng buộc cho bảng `gallery_reactions`
--
ALTER TABLE `gallery_reactions`
  ADD CONSTRAINT `gallery_reactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `gallery_reactions_ibfk_2` FOREIGN KEY (`gallery_id`) REFERENCES `gallery` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `global_chat`
--
ALTER TABLE `global_chat`
  ADD CONSTRAINT `global_chat_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `ideas`
--
ALTER TABLE `ideas`
  ADD CONSTRAINT `ideas_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Các ràng buộc cho bảng `idea_upvotes`
--
ALTER TABLE `idea_upvotes`
  ADD CONSTRAINT `idea_upvotes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `idea_upvotes_ibfk_2` FOREIGN KEY (`idea_id`) REFERENCES `ideas` (`id`);

--
-- Các ràng buộc cho bảng `ratings`
--
ALTER TABLE `ratings`
  ADD CONSTRAINT `ratings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `ratings_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
