from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Customer Table
        self.customer_table = dynamodb.Table(
            self, "CustomerTable",
            table_name="portfolio-tracker-customers",
            partition_key=dynamodb.Attribute(
                name="customer_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Portfolio Table
        self.portfolio_table = dynamodb.Table(
            self, "PortfolioTable",
            table_name="portfolio-tracker-portfolios",
            partition_key=dynamodb.Attribute(
                name="portfolio_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # GSI for querying portfolios by customer_id
        self.portfolio_table.add_global_secondary_index(
            index_name="customer-index",
            partition_key=dynamodb.Attribute(
                name="customer_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Investment Table
        self.investment_table = dynamodb.Table(
            self, "InvestmentTable",
            table_name="portfolio-tracker-investments",
            partition_key=dynamodb.Attribute(
                name="investment_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # GSI for querying investments by portfolio_id
        self.investment_table.add_global_secondary_index(
            index_name="portfolio-index",
            partition_key=dynamodb.Attribute(
                name="portfolio_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Basic IAM role for microservices
        self.microservice_role = iam.Role(
            self, "MicroserviceRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Grant DynamoDB permissions to microservice role
        self.customer_table.grant_read_write_data(self.microservice_role)
        self.portfolio_table.grant_read_write_data(self.microservice_role)
        self.investment_table.grant_read_write_data(self.microservice_role)

        # API Gateway
        self.api = apigateway.RestApi(
            self, "PortfolioTrackerApi",
            rest_api_name="Portfolio Tracker API",
            description="Investment Portfolio Tracker API Gateway",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"]
            )
        )

        # Mock integration for Customer Service (placeholder for ECS integration)
        self.customer_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '{"message": "Customer Service Mock Response", "method": "$context.httpMethod", "path": "$context.resourcePath"}'
                    },
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
            ],
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        # Customer API resource
        customers_resource = self.api.root.add_resource("customers")
        customers_resource.add_method(
            "GET", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        customers_resource.add_method(
            "POST", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="201",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Customer by ID resource
        customer_by_id = customers_resource.add_resource("{customer_id}")
        customer_by_id.add_method(
            "GET", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        customer_by_id.add_method(
            "PUT", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        customer_by_id.add_method(
            "DELETE", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Customer by email resource
        customer_email = customers_resource.add_resource("email").add_resource("{email}")
        customer_email.add_method(
            "GET", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Health check resource
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET", 
            self.customer_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Portfolio Service Integration (same mock for now)
        self.portfolio_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '{"message": "Portfolio Service Mock Response", "method": "$context.httpMethod", "path": "$context.resourcePath"}'
                    },
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
            ],
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        # Portfolio API resources
        portfolios_resource = self.api.root.add_resource("portfolios")
        portfolios_resource.add_method(
            "GET", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        portfolios_resource.add_method(
            "POST", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="201",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Portfolio by ID resource
        portfolio_by_id = portfolios_resource.add_resource("{portfolio_id}")
        portfolio_by_id.add_method(
            "GET", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        portfolio_by_id.add_method(
            "PUT", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        portfolio_by_id.add_method(
            "DELETE", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Customer portfolios resource (reuse existing customer_by_id)
        customer_portfolios = customer_by_id.add_resource("portfolios")
        customer_portfolios.add_method(
            "GET", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Customer portfolio summary resource
        customer_portfolio_summary = customer_portfolios.add_resource("summary")
        customer_portfolio_summary.add_method(
            "GET", 
            self.portfolio_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Asset Service Integration (same mock for now)
        self.asset_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '{"message": "Asset Service Mock Response", "method": "$context.httpMethod", "path": "$context.resourcePath"}'
                    },
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
            ],
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        # Investment API resources
        investments_resource = self.api.root.add_resource("investments")
        investments_resource.add_method(
            "GET", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        investments_resource.add_method(
            "POST", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="201",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Investment by ID resource
        investment_by_id = investments_resource.add_resource("{investment_id}")
        investment_by_id.add_method(
            "GET", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        investment_by_id.add_method(
            "PUT", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )
        investment_by_id.add_method(
            "DELETE", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Portfolio investments resource (reuse existing portfolio_by_id)
        portfolio_investments = portfolio_by_id.add_resource("investments")
        portfolio_investments.add_method(
            "GET", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Portfolio investment summary resource
        portfolio_investment_summary = portfolio_investments.add_resource("summary")
        portfolio_investment_summary.add_method(
            "GET", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Assets API resources
        assets_resource = self.api.root.add_resource("assets")
        
        # Asset price resource
        asset_ticker = assets_resource.add_resource("{ticker_symbol}")
        asset_price = asset_ticker.add_resource("price")
        asset_price.add_method(
            "GET", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # Batch prices resource
        asset_prices = assets_resource.add_resource("prices")
        asset_prices.add_method(
            "POST", 
            self.asset_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True
                    }
                )
            ]
        )

        # ECS Infrastructure
        # VPC for ECS cluster
        self.vpc = ec2.Vpc(
            self, "PortfolioTrackerVpc",
            max_azs=2,
            nat_gateways=1
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self, "PortfolioTrackerCluster",
            vpc=self.vpc,
            cluster_name="portfolio-tracker-cluster"
        )

        # ECR Repositories for each service
        self.customer_service_repo = ecr.Repository(
            self, "CustomerServiceRepo",
            repository_name="portfolio-tracker/customer-service",
            removal_policy=RemovalPolicy.DESTROY
        )

        self.portfolio_service_repo = ecr.Repository(
            self, "PortfolioServiceRepo",
            repository_name="portfolio-tracker/portfolio-service",
            removal_policy=RemovalPolicy.DESTROY
        )

        self.asset_service_repo = ecr.Repository(
            self, "AssetServiceRepo",
            repository_name="portfolio-tracker/asset-service",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "PortfolioTrackerALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="portfolio-tracker-alb"
        )

        # ALB Listener
        self.alb_listener = self.alb.add_listener(
            "ALBListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=200,
                content_type="application/json",
                message_body='{"message": "Portfolio Tracker API", "status": "healthy"}'
            )
        )

        # Security Groups for ECS Services
        self.customer_service_sg = ec2.SecurityGroup(
            self, "CustomerServiceSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
            description="Security group for Customer Service"
        )
        
        self.portfolio_service_sg = ec2.SecurityGroup(
            self, "PortfolioServiceSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
            description="Security group for Portfolio Service"
        )
        
        self.asset_service_sg = ec2.SecurityGroup(
            self, "AssetServiceSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
            description="Security group for Asset Service"
        )

        # Allow ALB to reach ECS services
        self.customer_service_sg.add_ingress_rule(
            peer=self.alb.connections.security_groups[0],
            connection=ec2.Port.tcp(8000),
            description="Allow ALB to reach Customer Service"
        )
        
        self.portfolio_service_sg.add_ingress_rule(
            peer=self.alb.connections.security_groups[0],
            connection=ec2.Port.tcp(8001),
            description="Allow ALB to reach Portfolio Service"
        )
        
        self.asset_service_sg.add_ingress_rule(
            peer=self.alb.connections.security_groups[0],
            connection=ec2.Port.tcp(8002),
            description="Allow ALB to reach Asset Service"
        )

        # Task Definitions and Services
        self._create_customer_service()
        self._create_portfolio_service()
        self._create_asset_service()
        
        # Create target groups and configure ALB routing
        self._configure_load_balancer_routing()

    def _create_customer_service(self):
        """Create Customer Service ECS task definition and service"""
        # Log Group
        customer_log_group = logs.LogGroup(
            self, "CustomerServiceLogGroup",
            log_group_name="/ecs/customer-service",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Task Definition
        customer_task_def = ecs.FargateTaskDefinition(
            self, "CustomerServiceTaskDef",
            memory_limit_mib=512,
            cpu=256,
            task_role=self.microservice_role,
            execution_role=self.microservice_role
        )

        # Container Definition
        customer_container = customer_task_def.add_container(
            "CustomerServiceContainer",
            image=ecs.ContainerImage.from_ecr_repository(self.customer_service_repo),
            memory_limit_mib=512,
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "PORT": "8000"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="customer-service",
                log_group=customer_log_group
            )
        )

        customer_container.add_port_mappings(
            ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)
        )

        # ECS Service
        self.customer_service = ecs.FargateService(
            self, "CustomerService",
            cluster=self.cluster,
            task_definition=customer_task_def,
            desired_count=1,
            service_name="customer-service",
            assign_public_ip=True,
            security_groups=[self.customer_service_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

    def _create_portfolio_service(self):
        """Create Portfolio Service ECS task definition and service"""
        # Log Group
        portfolio_log_group = logs.LogGroup(
            self, "PortfolioServiceLogGroup",
            log_group_name="/ecs/portfolio-service",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Task Definition
        portfolio_task_def = ecs.FargateTaskDefinition(
            self, "PortfolioServiceTaskDef",
            memory_limit_mib=512,
            cpu=256,
            task_role=self.microservice_role,
            execution_role=self.microservice_role
        )

        # Container Definition
        portfolio_container = portfolio_task_def.add_container(
            "PortfolioServiceContainer",
            image=ecs.ContainerImage.from_ecr_repository(self.portfolio_service_repo),
            memory_limit_mib=512,
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "PORT": "8001"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="portfolio-service",
                log_group=portfolio_log_group
            )
        )

        portfolio_container.add_port_mappings(
            ecs.PortMapping(container_port=8001, protocol=ecs.Protocol.TCP)
        )

        # ECS Service
        self.portfolio_service = ecs.FargateService(
            self, "PortfolioService",
            cluster=self.cluster,
            task_definition=portfolio_task_def,
            desired_count=1,
            service_name="portfolio-service",
            assign_public_ip=True,
            security_groups=[self.portfolio_service_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

    def _create_asset_service(self):
        """Create Asset Service ECS task definition and service"""
        # Log Group
        asset_log_group = logs.LogGroup(
            self, "AssetServiceLogGroup",
            log_group_name="/ecs/asset-service",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Task Definition
        asset_task_def = ecs.FargateTaskDefinition(
            self, "AssetServiceTaskDef",
            memory_limit_mib=512,
            cpu=256,
            task_role=self.microservice_role,
            execution_role=self.microservice_role
        )

        # Container Definition
        asset_container = asset_task_def.add_container(
            "AssetServiceContainer",
            image=ecs.ContainerImage.from_ecr_repository(self.asset_service_repo),
            memory_limit_mib=512,
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "PORT": "8002",
                "PORTFOLIO_SERVICE_URL": f"http://{self.alb.load_balancer_dns_name}"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="asset-service",
                log_group=asset_log_group
            )
        )

        asset_container.add_port_mappings(
            ecs.PortMapping(container_port=8002, protocol=ecs.Protocol.TCP)
        )

        # ECS Service
        self.asset_service = ecs.FargateService(
            self, "AssetService",
            cluster=self.cluster,
            task_definition=asset_task_def,
            desired_count=1,
            service_name="asset-service",
            assign_public_ip=True,
            security_groups=[self.asset_service_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

    def _configure_load_balancer_routing(self):
        """Configure ALB target groups and routing rules"""
        
        # Customer Service Target Group
        customer_target_group = elbv2.ApplicationTargetGroup(
            self, "CustomerServiceTargetGroup",
            target_group_name="customer-service-tg",
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=self.vpc,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                protocol=elbv2.Protocol.HTTP,
                port="8000",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=5
            )
        )
        
        # Portfolio Service Target Group
        portfolio_target_group = elbv2.ApplicationTargetGroup(
            self, "PortfolioServiceTargetGroup",
            target_group_name="portfolio-service-tg",
            port=8001,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=self.vpc,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                protocol=elbv2.Protocol.HTTP,
                port="8001",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=5
            )
        )
        
        # Asset Service Target Group
        asset_target_group = elbv2.ApplicationTargetGroup(
            self, "AssetServiceTargetGroup",
            target_group_name="asset-service-tg",
            port=8002,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=self.vpc,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                protocol=elbv2.Protocol.HTTP,
                port="8002",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=5
            )
        )
        
        # Associate ECS Services with Target Groups
        customer_target_group.add_target(self.customer_service)
        portfolio_target_group.add_target(self.portfolio_service)
        asset_target_group.add_target(self.asset_service)
        
        # ALB Listener Rules
        self.alb_listener.add_action(
            "CustomerServiceRule",
            priority=100,
            conditions=[
                elbv2.ListenerCondition.path_patterns(["/customers*"])
            ],
            action=elbv2.ListenerAction.forward([customer_target_group])
        )
        
        self.alb_listener.add_action(
            "PortfolioServiceRule",
            priority=200,
            conditions=[
                elbv2.ListenerCondition.path_patterns(["/portfolios*"])
            ],
            action=elbv2.ListenerAction.forward([portfolio_target_group])
        )
        
        self.alb_listener.add_action(
            "AssetServiceInvestmentsRule",
            priority=300,
            conditions=[
                elbv2.ListenerCondition.path_patterns(["/investments*"])
            ],
            action=elbv2.ListenerAction.forward([asset_target_group])
        )
        
        self.alb_listener.add_action(
            "AssetServiceAssetsRule",
            priority=400,
            conditions=[
                elbv2.ListenerCondition.path_patterns(["/assets*"])
            ],
            action=elbv2.ListenerAction.forward([asset_target_group])
        )
