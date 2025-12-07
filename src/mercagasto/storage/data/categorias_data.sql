-- =============================================================================
-- DATOS DE CATEGORÍAS Y SUBCATEGORÍAS DE MERCADONA
-- =============================================================================
-- 
-- Este archivo contiene los datos de categorías y subcategorías extraídos
-- del archivo categorias.json para cargar en la base de datos.
--
-- Fecha: 2025-12-07
-- Origen: categorias.json
-- Base de datos: PostgreSQL
-- =============================================================================

-- Limpiar datos existentes (opcional, descomentar si se desea resetear)
-- DELETE FROM subcategorias;
-- DELETE FROM categorias;

-- =============================================================================
-- INSERCIÓN DE CATEGORÍAS PRINCIPALES
-- =============================================================================

INSERT INTO categorias (id, nombre, orden, is_extended) VALUES
(12, 'Aceite, especias y salsas', 7, false),
(18, 'Agua y refrescos', 8, false),
(15, 'Aperitivos', 9, false),
(13, 'Arroz, legumbres y pasta', 10, false),
(9, 'Azúcar, caramelos y chocolate', 11, false),
(24, 'Bebé', 14, false),
(19, 'Bodega', 15, false),
(8, 'Cacao, café e infusiones', 16, false),
(3, 'Carne', 17, false),
(7, 'Cereales y galletas', 18, false),
(4, 'Charcutería y quesos', 159, false),
(17, 'Congelados', 213, false),
(14, 'Conservas, caldos y cremas', 215, false),
(21, 'Cuidado del cabello', 238, false),
(20, 'Cuidado facial y corporal', 241, false),
(23, 'Fitoterapia y parafarmacia', 305, false),
(1, 'Fruta y verdura', 306, false),
(6, 'Huevos, leche y mantequilla', 373, false),
(26, 'Limpieza y hogar', 374, false),
(22, 'Maquillaje', 422, false),
(2, 'Marisco y pescado', 442, false),
(25, 'Mascotas', 443, false),
(5, 'Panadería y pastelería', 515, false),
(16, 'Pizzas y platos preparados', 597, false),
(11, 'Postres y yogures', 598, false),
(10, 'Zumos', 793, false)
ON CONFLICT (id) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    orden = EXCLUDED.orden,
    is_extended = EXCLUDED.is_extended,
    updated_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- INSERCIÓN DE SUBCATEGORÍAS
-- =============================================================================

-- Subcategorías de "Aceite, especias y salsas" (id: 12)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(112, 12, 'Aceite, vinagre y sal', 7, 1, true, false),
(115, 12, 'Especias', 7, 1, true, false),
(116, 12, 'Mayonesa, ketchup y mostaza', 7, 1, true, false),
(117, 12, 'Otras salsas', 7, 1, true, false);

-- Subcategorías de "Agua y refrescos" (id: 18)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(156, 18, 'Agua', 8, 1, true, false),
(163, 18, 'Isotónico y energético', 8, 1, true, false),
(158, 18, 'Refresco de cola', 8, 1, true, false),
(159, 18, 'Refresco de naranja y de limón', 8, 1, true, false),
(161, 18, 'Tónica y bitter', 8, 1, true, false),
(162, 18, 'Refresco de té y sin gas', 8, 1, true, false);

-- Subcategorías de "Aperitivos" (id: 15)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(135, 15, 'Aceitunas y encurtidos', 9, 1, true, false),
(133, 15, 'Frutos secos y fruta desecada', 9, 1, true, false),
(132, 15, 'Patatas fritas y snacks', 9, 1, true, false);

-- Subcategorías de "Arroz, legumbres y pasta" (id: 13)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(118, 13, 'Arroz', 10, 1, true, false),
(121, 13, 'Legumbres', 10, 1, true, false),
(120, 13, 'Pasta y fideos', 10, 1, true, false);

-- Subcategorías de "Azúcar, caramelos y chocolate" (id: 9)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(89, 9, 'Azúcar y edulcorante', 11, 1, true, false),
(95, 9, 'Chicles y caramelos', 11, 1, true, false),
(92, 9, 'Chocolate', 11, 1, true, false),
(97, 9, 'Golosinas', 11, 1, true, false),
(90, 9, 'Mermelada y miel', 11, 1, true, false),
(833, 9, 'Turrones', 11, 1, true, false);

-- Subcategorías de "Bebé" (id: 24)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(216, 24, 'Alimentación infantil', 14, 1, true, false),
(219, 24, 'Biberón y chupete', 14, 1, true, false),
(218, 24, 'Higiene y cuidado', 14, 1, true, false),
(217, 24, 'Toallitas y pañales', 14, 1, true, false);

-- Subcategorías de "Bodega" (id: 19)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(164, 19, 'Cerveza', 15, 1, true, false),
(166, 19, 'Cerveza sin alcohol', 15, 1, true, false),
(181, 19, 'Licores', 15, 1, true, false),
(174, 19, 'Sidra y cava', 15, 1, true, false),
(168, 19, 'Tinto de verano y sangría', 15, 1, true, false),
(170, 19, 'Vino blanco', 15, 1, true, false),
(173, 19, 'Vino lambrusco y espumoso', 15, 1, true, false),
(171, 19, 'Vino rosado', 15, 1, true, false),
(169, 19, 'Vino tinto', 15, 1, true, false);

-- Subcategorías de "Cacao, café e infusiones" (id: 8)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(86, 8, 'Cacao soluble y chocolate a la taza', 16, 1, true, false),
(81, 8, 'Café cápsula y monodosis', 16, 1, true, false),
(83, 8, 'Café molido y en grano', 16, 1, true, false),
(84, 8, 'Café soluble y otras bebidas', 16, 1, true, false),
(88, 8, 'Té e infusiones', 16, 1, true, false);

-- Subcategorías de "Carne" (id: 3)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(46, 3, 'Arreglos', 17, 1, true, false),
(38, 3, 'Aves y pollo', 17, 1, true, false),
(47, 3, 'Carne congelada', 17, 1, true, false),
(37, 3, 'Cerdo', 17, 1, true, false),
(42, 3, 'Conejo y cordero', 17, 1, true, false),
(43, 3, 'Embutido', 17, 1, true, false),
(44, 3, 'Hamburguesas y picadas', 17, 1, true, false),
(40, 3, 'Vacuno', 17, 1, true, false),
(45, 3, 'Empanados y elaborados', 17, 1, true, false);

-- Subcategorías de "Cereales y galletas" (id: 7)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(78, 7, 'Cereales', 18, 1, true, false),
(80, 7, 'Galletas', 18, 1, true, false),
(79, 7, 'Tortitas', 18, 1, true, false);

-- Subcategorías de "Charcutería y quesos" (id: 4)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(48, 4, 'Aves y jamón cocido', 159, 1, true, false),
(52, 4, 'Bacón y salchichas', 159, 1, true, false),
(49, 4, 'Chopped y mortadela', 159, 1, true, false),
(51, 4, 'Embutido curado', 159, 1, true, false),
(50, 4, 'Jamón serrano', 159, 1, true, false),
(58, 4, 'Paté y sobrasada', 159, 1, true, false),
(54, 4, 'Queso curado, semicurado y tierno', 159, 1, true, false),
(56, 4, 'Queso lonchas, rallado y en porciones', 159, 1, true, false),
(53, 4, 'Queso untable y fresco', 159, 1, true, false);

-- Subcategorías de "Congelados" (id: 17)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(147, 17, 'Arroz y pasta', 213, 1, true, false),
(148, 17, 'Carne', 213, 1, true, false),
(154, 17, 'Helados', 213, 1, true, false),
(155, 17, 'Hielo', 213, 1, true, false),
(150, 17, 'Marisco', 213, 1, true, false),
(149, 17, 'Pescado', 213, 1, true, false),
(151, 17, 'Pizzas', 213, 1, true, false),
(884, 17, 'Rebozados', 213, 2, true, false),
(152, 17, 'Tartas y churros', 213, 1, true, false),
(145, 17, 'Verdura', 213, 1, true, false);

-- Subcategorías de "Conservas, caldos y cremas" (id: 14)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(122, 14, 'Atún y otras conservas de pescado', 215, 1, true, false),
(123, 14, 'Berberechos y mejillones', 215, 1, true, false),
(127, 14, 'Conservas de verdura y frutas', 215, 1, true, false),
(130, 14, 'Gazpacho y cremas', 215, 1, true, false),
(129, 14, 'Sopa y caldo', 215, 1, true, false),
(126, 14, 'Tomate', 215, 1, true, false);

-- Subcategorías de "Cuidado del cabello" (id: 21)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(201, 21, 'Acondicionador y mascarilla', 238, 1, true, false),
(199, 21, 'Champú', 238, 1, true, false),
(203, 21, 'Coloración cabello', 238, 1, true, false),
(202, 21, 'Fijación cabello', 238, 1, true, false);

-- Subcategorías de "Cuidado facial y corporal" (id: 20)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(192, 20, 'Afeitado y cuidado para hombre', 241, 1, true, false),
(189, 20, 'Cuidado corporal', 241, 1, true, false),
(185, 20, 'Cuidado e higiene facial', 241, 1, true, false),
(191, 20, 'Depilación', 241, 1, true, false),
(188, 20, 'Desodorante', 241, 1, true, false),
(187, 20, 'Gel y jabón de manos', 241, 1, true, false),
(186, 20, 'Higiene bucal', 241, 1, true, false),
(190, 20, 'Higiene íntima', 241, 1, true, false),
(194, 20, 'Manicura y pedicura', 241, 1, true, false),
(196, 20, 'Perfume y colonia', 241, 1, true, false),
(198, 20, 'Protector solar y aftersun', 241, 1, true, false);

-- Subcategorías de "Fitoterapia y parafarmacia" (id: 23)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(213, 23, 'Fitoterapia', 305, 1, true, false),
(214, 23, 'Parafarmacia', 305, 1, true, false);

-- Subcategorías de "Fruta y verdura" (id: 1)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(27, 1, 'Fruta', 306, 1, true, false),
(28, 1, 'Lechuga y ensalada preparada', 306, 1, true, false),
(29, 1, 'Verdura', 306, 1, true, false);

-- Subcategorías de "Huevos, leche y mantequilla" (id: 6)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(77, 6, 'Huevos', 373, 1, true, false),
(72, 6, 'Leche y bebidas vegetales', 373, 1, true, false),
(75, 6, 'Mantequilla y margarina', 373, 1, true, false);

-- Subcategorías de "Limpieza y hogar" (id: 26)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(226, 26, 'Detergente y suavizante ropa', 374, 1, true, false),
(237, 26, 'Estropajo, bayeta y guantes', 374, 1, true, false),
(241, 26, 'Insecticida y ambientador', 374, 1, true, false),
(234, 26, 'Lejía y líquidos fuertes', 374, 1, true, false),
(235, 26, 'Limpiacristales', 374, 1, true, false),
(233, 26, 'Limpiahogar y friegasuelos', 374, 1, true, false),
(231, 26, 'Limpieza baño y WC', 374, 1, true, false),
(230, 26, 'Limpieza cocina', 374, 1, true, false),
(232, 26, 'Limpieza muebles y multiusos', 374, 1, true, false),
(229, 26, 'Limpieza vajilla', 374, 1, true, false),
(243, 26, 'Menaje y conservación de alimentos', 374, 1, true, false),
(238, 26, 'Papel higiénico y celulosa', 374, 1, true, false),
(239, 26, 'Pilas y bolsas de basura', 374, 1, true, false),
(244, 26, 'Utensilios de limpieza y calzado', 374, 1, true, false);

-- Subcategorías de "Maquillaje" (id: 22)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(206, 22, 'Bases de maquillaje y corrector', 422, 1, true, false),
(207, 22, 'Colorete y polvos', 422, 1, true, false),
(208, 22, 'Labios', 422, 1, true, false),
(210, 22, 'Ojos', 422, 1, true, false),
(212, 22, 'Pinceles y brochas', 422, 1, true, false);

-- Subcategorías de "Marisco y pescado" (id: 2)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(32, 2, 'Marisco', 442, 1, true, false),
(34, 2, 'Pescado congelado', 442, 1, true, false),
(31, 2, 'Pescado fresco', 442, 1, true, false),
(36, 2, 'Salazones y ahumados', 442, 1, true, false);

-- Subcategorías de "Mascotas" (id: 25)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(222, 25, 'Gato', 443, 1, true, false),
(221, 25, 'Perro', 443, 1, true, false),
(225, 25, 'Otros', 443, 1, true, false);

-- Subcategorías de "Panadería y pastelería" (id: 5)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(65, 5, 'Bollería de horno', 515, 1, true, false),
(66, 5, 'Bollería envasada', 515, 1, true, false),
(69, 5, 'Harina y preparado repostería', 515, 1, true, false),
(59, 5, 'Pan de horno', 515, 1, true, false),
(60, 5, 'Pan de molde y otras especialidades', 515, 1, true, false),
(62, 5, 'Pan tostado y rallado', 515, 1, true, false),
(64, 5, 'Picos, rosquilletas y picatostes', 515, 1, true, false),
(68, 5, 'Tartas y pasteles', 515, 1, true, false),
(71, 5, 'Velas y decoración', 515, 1, true, false);

-- Subcategorías de "Pizzas y platos preparados" (id: 16)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(897, 16, 'Listo para Comer', 597, 1, true, false),
(138, 16, 'Pizzas', 597, 1, true, false),
(140, 16, 'Platos preparados calientes', 597, 1, true, false),
(142, 16, 'Platos preparados fríos', 597, 1, true, false);

-- Subcategorías de "Postres y yogures" (id: 11)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(105, 11, 'Bífidus', 598, 1, true, false),
(110, 11, 'Flan y natillas', 598, 1, true, false),
(111, 11, 'Gelatina y otros postres', 598, 1, true, false),
(106, 11, 'Postres de soja', 598, 1, true, false),
(103, 11, 'Yogures desnatados', 598, 1, true, false),
(109, 11, 'Yogures griegos', 598, 1, true, false),
(108, 11, 'Yogures líquidos', 598, 1, true, false),
(104, 11, 'Yogures naturales y sabores', 598, 1, true, false),
(107, 11, 'Yogures y postres infantiles', 598, 1, true, false);

-- Subcategorías de "Zumos" (id: 10)
INSERT INTO subcategorias (id, categoria_id, nombre, orden, layout, published, is_extended) VALUES
(99, 10, 'Fruta variada', 793, 1, true, false),
(100, 10, 'Melocotón y piña', 793, 1, true, false),
(143, 10, 'Naranja', 793, 1, true, false),
(98, 10, 'Tomate y otros sabores', 793, 1, true, false);

-- Manejar conflictos en subcategorías con UPSERT
ON CONFLICT (id) DO UPDATE SET
    categoria_id = EXCLUDED.categoria_id,
    nombre = EXCLUDED.nombre,
    orden = EXCLUDED.orden,
    layout = EXCLUDED.layout,
    published = EXCLUDED.published,
    is_extended = EXCLUDED.is_extended,
    updated_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- VERIFICACIÓN DE DATOS INSERTADOS
-- =============================================================================

-- Verificar el total de categorías insertadas
SELECT 'Categorías' as tabla, COUNT(*) as total FROM categorias
UNION ALL
SELECT 'Subcategorías' as tabla, COUNT(*) as total FROM subcategorias;

-- Mostrar categorías con el número de subcategorías
SELECT 
    c.id,
    c.nombre as categoria,
    c.orden,
    COUNT(s.id) as num_subcategorias
FROM categorias c
LEFT JOIN subcategorias s ON c.id = s.categoria_id
GROUP BY c.id, c.nombre, c.orden
ORDER BY c.orden;

-- =============================================================================
-- FIN DEL ARCHIVO DE DATOS
-- =============================================================================