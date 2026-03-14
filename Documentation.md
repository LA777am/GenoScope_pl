⸻

Deployment & Infrastructure

GenoScope is deployed as a cloud-based genomic analysis platform accessible through a publicly hosted environment.

Live Deployment

https://genotech-genoscope.hf.space/

The system is hosted using Hugging Face Spaces, which provides containerized deployment for Python-based applications.

⸻

Cloud Infrastructure

Component	Technology	Purpose
Application Hosting	Hugging Face Spaces	Containerized web deployment
Backend Framework	Flask	REST API and application logic
Database	Neon PostgreSQL	Cloud-hosted relational database
Authentication	Google OAuth 2.0	Secure user identity verification
Machine Learning	Scikit-learn	Genomic classification models
Visualization	3Dmol.js	Interactive protein structure visualization


⸻

Hosting Platform

Hugging Face Spaces

The GenoScope application is deployed on Hugging Face Spaces using a Docker-based runtime.

Hugging Face Spaces provides:
	•	containerized execution environment
	•	automatic build and deployment
	•	public web hosting
	•	GPU / CPU execution environments
	•	integrated repository version control

Application access:

https://genotech-genoscope.hf.space/

The platform runs the Flask application inside a container and exposes the service through the configured application port.

⸻

Cloud Database

Neon PostgreSQL

GenoScope uses Neon, a serverless PostgreSQL platform, for persistent data storage.

Neon provides:
	•	serverless PostgreSQL architecture
	•	automatic scaling
	•	cloud-based database management
	•	connection pooling
	•	high availability

The database stores:

Table	Purpose
users	registered user accounts
sequences	submitted DNA sequences
analyses	computed analysis results
predictions	machine learning outputs
batches	batch processing records
comparisons	sequence comparison history

Database connections are established through the PostgreSQL connection URI provided by Neon.

⸻

Authentication System

Google OAuth 2.0

User authentication is implemented using Google Identity Services, configured through Google Cloud Console.

Authentication workflow:
	1.	User selects Sign in with Google
	2.	Google Identity Services returns a secure ID token
	3.	Backend verifies token using Google’s authentication libraries
	4.	User identity is validated
	5.	Session is established on the server

Token verification is performed using:

google.oauth2.id_token.verify_oauth2_token()

This ensures:
	•	secure authentication
	•	identity verification through Google
	•	no password storage in the application database
	•	reduced security risk

⸻

Environment Configuration

Deployment requires the following environment variables:

Variable	Description
DATABASE_URL	Neon PostgreSQL connection string
GOOGLE_CLIENT_ID	Google OAuth client ID
SECRET_KEY	Flask session encryption key

Example configuration:

DATABASE_URL=postgresql://user:password@neon-host/dbname
GOOGLE_CLIENT_ID=your-google-oauth-client-id
SECRET_KEY=secure-session-key


⸻

System Availability

The platform is accessible through any modern web browser capable of running JavaScript and WebGL.

Due to the use of high-fidelity genomic visualizations and molecular structure rendering, the application is optimized for desktop-class displays.

Mobile environments may restrict full functionality.

⸻

Deployment Architecture

User Browser
     │
     ▼
Hugging Face Spaces (Flask Application)
     │
     ├── Machine Learning Models
     ├── Mutation Detection Engine
     ├── Sequence Analysis Pipeline
     │
     ▼
Neon PostgreSQL Cloud Database

Authentication flow:

User → Google OAuth → Token Verification → Flask Session


⸻

Production Notes

The deployed platform is configured for:
	•	secure OAuth authentication
	•	cloud-hosted persistent storage
	•	containerized application execution
	•	real-time genomic analysis

The architecture allows the system to be extended with additional models, reference genomes, or visualization modules without major infrastructure changes.

⸻