// Script MongoDB para actualizar permisos del Super Administrador
// Ejecutar en: mongo mi_app_completa_db

use mi_app_completa_db;

// Ver permisos actuales del Super Admin
print("📊 Permisos actuales del Super Administrador:");
var superAdmin = db.roles.findOne({name: "super_admin"});
if (superAdmin) {
    print("Permisos actuales: " + superAdmin.permissions.length);
    superAdmin.permissions.forEach(function(perm) {
        print("  - " + perm);
    });
} else {
    print("❌ Super Admin no encontrado");
}

// Agregar el permiso modules.techo_propio
print("\n🔧 Agregando permiso modules.techo_propio...");
var result = db.roles.updateOne(
    {name: "super_admin"},
    {
        $addToSet: {
            permissions: "modules.techo_propio"
        },
        $set: {
            updated_at: new Date().toISOString()
        }
    }
);

print("Resultado: " + result.modifiedCount + " documento(s) modificado(s)");

// Verificar que se agregó correctamente
print("\n✅ Verificando cambios:");
var updatedSuperAdmin = db.roles.findOne({name: "super_admin"});
if (updatedSuperAdmin) {
    print("Permisos después: " + updatedSuperAdmin.permissions.length);
    var hasTechoPropio = updatedSuperAdmin.permissions.includes("modules.techo_propio");
    print("Tiene modules.techo_propio: " + (hasTechoPropio ? "✅ SÍ" : "❌ NO"));
} else {
    print("❌ Error: Super Admin no encontrado después de la actualización");
}