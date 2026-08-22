// Los decoradores de class-validator / class-transformer / Nest necesitan el
// polyfill de metadata. En produccion lo carga Nest al arrancar; en Jest hay
// que cargarlo explicitamente antes de cualquier suite.
import 'reflect-metadata';
