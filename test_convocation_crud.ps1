# 🧪 Script de Testing Completo - Operaciones CRUD Convocatorias
# Ejecutar: .\test_convocation_crud.ps1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🧪 TESTING COMPLETO - CONVOCATORIAS TECHO PROPIO        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ==================== CONFIGURACIÓN ====================

$baseUrl = "http://localhost:8000/api/techo-propio/convocations"
$token = $null

# Obtener token del usuario
Write-Host "🔐 Configuración de autenticación" -ForegroundColor Yellow
Write-Host "Por favor ingresa tu token de autenticación:" -ForegroundColor White
Write-Host "(Puedes obtenerlo desde el navegador: DevTools > Console > localStorage.getItem('auth_token'))" -ForegroundColor Gray
Write-Host ""
$token = Read-Host "Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "❌ ERROR: Token no proporcionado. Abortando." -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Variables para tracking
$testsPassed = 0
$testsFailed = 0
$convId = $null

# ==================== FUNCIONES AUXILIARES ====================

function Test-Step {
    param (
        [string]$Name,
        [scriptblock]$Action
    )
    
    Write-Host ""
    Write-Host "▶ $Name" -ForegroundColor Cyan
    Write-Host ("─" * 60) -ForegroundColor Gray
    
    try {
        $result = & $Action
        $script:testsPassed++
        Write-Host "✅ ÉXITO" -ForegroundColor Green
        return $result
    }
    catch {
        $script:testsFailed++
        Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        
        # Mostrar detalles del error si es HTTPException
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
            
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                $reader.Close()
                Write-Host "   Detalle: $responseBody" -ForegroundColor Yellow
            }
            catch {
                # Ignorar errores al leer el cuerpo de la respuesta
            }
        }
        
        return $null
    }
}

# ==================== TESTS ====================

Write-Host "🏁 Iniciando tests..." -ForegroundColor White
Write-Host ""

# TEST 0: Health Check
Test-Step "TEST 0: Health Check (sin autenticación)" {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "   Status: $($data.status)" -ForegroundColor White
    Write-Host "   Module: $($data.module)" -ForegroundColor White
    Write-Host "   Version: $($data.version)" -ForegroundColor White
    
    if ($data.status -ne "healthy") {
        throw "El módulo no está saludable"
    }
}

# TEST 1: Listar Convocatorias
Test-Step "TEST 1: Listar Convocatorias" {
    $response = Invoke-WebRequest -Uri "$baseUrl/" -Method GET -Headers $headers
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "   Total de convocatorias: $($data.total)" -ForegroundColor White
    Write-Host "   En esta página: $($data.convocations.Count)" -ForegroundColor White
    
    if ($data.convocations.Count -gt 0) {
        Write-Host "   Primera: $($data.convocations[0].code) - $($data.convocations[0].title)" -ForegroundColor Gray
    }
}

# TEST 2: Crear Convocatoria
$script:convId = Test-Step "TEST 2: Crear Nueva Convocatoria" {
    $timestamp = Get-Date -Format "HHmmss"
    
    $newConv = @{
        code = "CONV-2025-TEST-$timestamp"
        title = "Convocatoria de Prueba CRUD"
        description = "Convocatoria creada automáticamente para testing de operaciones CRUD"
        start_date = "2025-11-01"
        end_date = "2025-12-31"
        is_active = $true
        is_published = $false
        max_applications = 100
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/" -Method POST -Headers $headers -Body $newConv
    $created = $response.Content | ConvertFrom-Json
    
    Write-Host "   ID: $($created.id)" -ForegroundColor White
    Write-Host "   Código: $($created.code)" -ForegroundColor White
    Write-Host "   Título: $($created.title)" -ForegroundColor White
    Write-Host "   Activa: $($created.is_active)" -ForegroundColor White
    Write-Host "   Publicada: $($created.is_published)" -ForegroundColor White
    
    return $created.id
}

if (-not $convId) {
    Write-Host ""
    Write-Host "❌ ABORTANDO: No se pudo crear la convocatoria de prueba" -ForegroundColor Red
    exit 1
}

# TEST 3: Obtener por ID
Test-Step "TEST 3: Obtener Convocatoria por ID" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId" -Method GET -Headers $headers
    $conv = $response.Content | ConvertFrom-Json
    
    Write-Host "   ID: $($conv.id)" -ForegroundColor White
    Write-Host "   Código: $($conv.code)" -ForegroundColor White
    Write-Host "   Título: $($conv.title)" -ForegroundColor White
    Write-Host "   Estado: $($conv.status_display)" -ForegroundColor White
    
    if ($conv.id -ne $convId) {
        throw "El ID no coincide"
    }
}

# TEST 4: Actualizar Convocatoria (incluyendo is_published)
Test-Step "TEST 4: Actualizar Convocatoria (CRÍTICO)" {
    $updates = @{
        title = "Convocatoria EDITADA ✅"
        description = "Descripción actualizada mediante testing automático"
        is_published = $true
        is_active = $true
        max_applications = 200
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId" -Method PUT -Headers $headers -Body $updates
    $updated = $response.Content | ConvertFrom-Json
    
    Write-Host "   Título actualizado: $($updated.title)" -ForegroundColor White
    Write-Host "   Publicada: $($updated.is_published)" -ForegroundColor White
    Write-Host "   Activa: $($updated.is_active)" -ForegroundColor White
    Write-Host "   Max solicitudes: $($updated.max_applications)" -ForegroundColor White
    
    if (-not $updated.is_published) {
        throw "El campo is_published no se actualizó correctamente"
    }
    
    if ($updated.title -notmatch "EDITADA") {
        throw "El título no se actualizó correctamente"
    }
}

# TEST 5: Verificar Actualización
Test-Step "TEST 5: Verificar que los cambios se guardaron" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId" -Method GET -Headers $headers
    $conv = $response.Content | ConvertFrom-Json
    
    Write-Host "   Título: $($conv.title)" -ForegroundColor White
    Write-Host "   Publicada: $($conv.is_published)" -ForegroundColor White
    
    if (-not $conv.is_published) {
        throw "Los cambios no se persistieron correctamente"
    }
}

# TEST 6: Activar Convocatoria
Test-Step "TEST 6: Activar Convocatoria" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId/activate" -Method PATCH -Headers $headers
    $activated = $response.Content | ConvertFrom-Json
    
    Write-Host "   Activa: $($activated.is_active)" -ForegroundColor White
    
    if (-not $activated.is_active) {
        throw "La convocatoria no se activó"
    }
}

# TEST 7: Desactivar Convocatoria
Test-Step "TEST 7: Desactivar Convocatoria" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId/deactivate" -Method PATCH -Headers $headers
    $deactivated = $response.Content | ConvertFrom-Json
    
    Write-Host "   Activa: $($deactivated.is_active)" -ForegroundColor White
    
    if ($deactivated.is_active) {
        throw "La convocatoria no se desactivó"
    }
}

# TEST 8: Publicar Convocatoria
Test-Step "TEST 8: Publicar Convocatoria" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId/publish" -Method PATCH -Headers $headers
    $published = $response.Content | ConvertFrom-Json
    
    Write-Host "   Publicada: $($published.is_published)" -ForegroundColor White
    
    if (-not $published.is_published) {
        throw "La convocatoria no se publicó"
    }
}

# TEST 9: Eliminar Convocatoria
Test-Step "TEST 9: Eliminar Convocatoria" {
    $response = Invoke-WebRequest -Uri "$baseUrl/$convId" -Method DELETE -Headers $headers
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "   Mensaje: $($result.message)" -ForegroundColor White
}

# TEST 10: Verificar que se eliminó
Test-Step "TEST 10: Verificar que se eliminó" {
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/$convId" -Method GET -Headers $headers
        throw "La convocatoria aún existe (debería haber sido eliminada)"
    }
    catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            Write-Host "   Convocatoria correctamente eliminada (404 Not Found)" -ForegroundColor White
        }
        else {
            throw
        }
    }
}

# ==================== RESULTADOS ====================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    RESULTADOS FINALES                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$totalTests = $testsPassed + $testsFailed

Write-Host "Total de tests ejecutados: $totalTests" -ForegroundColor White
Write-Host "✅ Tests exitosos: $testsPassed" -ForegroundColor Green
Write-Host "❌ Tests fallidos: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ El módulo de convocatorias está funcionando correctamente" -ForegroundColor Green
    Write-Host "✅ Operación CREATE funciona" -ForegroundColor Green
    Write-Host "✅ Operación READ funciona" -ForegroundColor Green
    Write-Host "✅ Operación UPDATE funciona (incluyendo is_published)" -ForegroundColor Green
    Write-Host "✅ Operación DELETE funciona" -ForegroundColor Green
    Write-Host "✅ Operaciones de estado (activar/desactivar/publicar) funcionan" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "⚠️  Algunos tests fallaron. Revisa los errores arriba." -ForegroundColor Yellow
    exit 1
}
