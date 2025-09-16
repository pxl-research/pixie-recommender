# Step 8: Docker Compose Uitbreiden met PostgreSQL

## Objective
Integreer PostgreSQL in development environment via Docker Compose en setup database initialization.

## Prerequisites
- Previous step completed: Integration tests implementeren
- Required tools/dependencies: Docker, Docker Compose, PostgreSQL image

## Actions
1. **Docker Compose configuratie updaten**
   - Update `docker-compose.dev.yml` met PostgreSQL service
   - Setup database volumes voor data persistence
   - Configureer netwerk connecties tussen services
   - Setup environment variables voor database connection

2. **Database initialization scripts**
   - Creëer `infra/docker/postgres/` directory
   - Implementeer database initialization SQL scripts
   - Setup database seeding met test data
   - Implementeer schema creation en migration scripts

3. **Development environment setup**
   - Update API service voor database dependency
   - Setup proper service startup ordering
   - Implementeer health checks voor database readiness
   - Setup database connection validation

4. **Data seeding en fixtures**
   - Migreer huidige JSON data naar SQL seeding scripts
   - Implementeer database fixtures voor development
   - Setup test data loading voor different scenarios
   - Implementeer data reset en cleanup scripts

5. **Environment configuration**
   - Setup proper environment variables voor development
   - Implementeer database URL configuration
   - Setup connection pooling parameters
   - Configureer logging en monitoring

6. **Documentation en workflows**
   - Update README.md met nieuwe database setup instructions
   - Documenteer development workflow changes
   - Update CI/CD workflows voor database testing
   - Implementeer database backup en restore procedures

## Success Criteria
- PostgreSQL draait correct in Docker Compose
- Database initialization werkt automatisch
- API kan connecten met database in container
- Development workflow is smooth en gedocumenteerd
- Test data loading werkt correct

## Next Step
Continue to: `09-production-config.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
