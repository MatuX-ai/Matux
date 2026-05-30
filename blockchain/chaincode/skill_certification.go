package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SkillCertificate 可验证技能证书结构
type SkillCertificate struct {
	ID              string    `json:"id"`
	HolderDID       string    `json:"holderDid"`       // 持有者DID
	IssuerDID       string    `json:"issuerDid"`       // 颁发者DID
	CredentialType  string    `json:"credentialType"`  // 凭证类型
	SkillName       string    `json:"skillName"`       // 技能名称
	SkillLevel      string    `json:"skillLevel"`      // 技能等级
	IssueDate       string    `json:"issueDate"`       // 颁发日期
	ExpiryDate      string    `json:"expiryDate"`      // 过期日期
	Evidence        []string  `json:"evidence"`        // 证明材料
	Status          string    `json:"status"`          // 状态(active/revoked)
	Metadata        VCProof   `json:"proof"`           // 数字签名证明
}

// VCProof W3C VC数字签名证明
type VCProof struct {
	Type               string `json:"type"`
	Created            string `json:"created"`
	VerificationMethod string `json:"verificationMethod"`
	ProofPurpose       string `json:"proofPurpose"`
	Jws                string `json:"jws"`
	RevocationReason   string `json:"revocationReason,omitempty"` // 撤销原因
}

// CertificationRequest 技能认证请求
type CertificationRequest struct {
	RequestID       string   `json:"requestId"`
	HolderDID       string   `json:"holderDid"`
	SkillName       string   `json:"skillName"`
	SkillLevel      string   `json:"skillLevel"`
	Evidence        []string `json:"evidence"`
	RequestDate     string   `json:"requestDate"`
	Status          string   `json:"status"` // pending/approved/rejected
	IssuerDID       string   `json:"issuerDID,omitempty"`
	ReviewComments  string   `json:"reviewComments,omitempty"`
}

// SkillChaincode 技能认证链码
type SkillChaincode struct {
	contractapi.Contract
}

// InitLedger 初始化账本
func (s *SkillChaincode) InitLedger(ctx contractapi.TransactionContextInterface) error {
	log.Println("初始化技能认证账本")

	// 创建一些示例证书用于测试
	certificates := []SkillCertificate{
		{
			ID:             "cert001",
			HolderDID:      "did:example:user001",
			IssuerDID:      "did:example:org001",
			CredentialType: "SkillCertificate",
			SkillName:      "区块链开发",
			SkillLevel:     "专家级",
			IssueDate:      time.Now().Format(time.RFC3339),
			ExpiryDate:     time.Now().AddDate(2, 0, 0).Format(time.RFC3339),
			Evidence:       []string{"项目经验", "认证考试"},
			Status:         "active",
			Metadata: VCProof{
				Type:               "Ed25519Signature2020",
				Created:            time.Now().Format(time.RFC3339),
				VerificationMethod: "did:example:org001#keys-1",
				ProofPurpose:       "assertionMethod",
				Jws:                "eyJhb...signature...",
			},
		},
	}

	for _, cert := range certificates {
		certJSON, err := json.Marshal(cert)
		if err != nil {
			return err
		}

		err = ctx.GetStub().PutState(cert.ID, certJSON)
		if err != nil {
			return fmt.Errorf("failed to put to world state: %v", err)
		}
	}

	return nil
}

// IssueCert 颁发证书
func (s *SkillChaincode) IssueCert(ctx contractapi.TransactionContextInterface, certJSON string) error {
	log.Printf("颁发证书: %s", certJSON)

	var cert SkillCertificate
	err := json.Unmarshal([]byte(certJSON), &cert)
	if err != nil {
		return fmt.Errorf("invalid certificate JSON: %v", err)
	}

	// 验证必需字段
	if cert.ID == "" || cert.HolderDID == "" || cert.IssuerDID == "" {
		return fmt.Errorf("missing required fields: id, holderDid, issuerDid")
	}

	// 检查证书是否已存在
	exists, err := s.CertExists(ctx, cert.ID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("certificate %s already exists", cert.ID)
	}

	// 设置默认值
	if cert.Status == "" {
		cert.Status = "active"
	}
	if cert.CredentialType == "" {
		cert.CredentialType = "SkillCertificate"
	}
	if cert.IssueDate == "" {
		cert.IssueDate = time.Now().Format(time.RFC3339)
	}
	if cert.ExpiryDate == "" {
		// 默认有效期2年
		cert.ExpiryDate = time.Now().AddDate(2, 0, 0).Format(time.RFC3339)
	}

	// 存储证书
	certBytes, err := json.Marshal(cert)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(cert.ID, certBytes)
}

// RevokeCert 撤销证书
func (s *SkillChaincode) RevokeCert(ctx contractapi.TransactionContextInterface, certID string, reason string) error {
	log.Printf("撤销证书: %s, 原因: %s", certID, reason)

	cert, err := s.GetCert(ctx, certID)
	if err != nil {
		return err
	}

	// 检查证书状态
	if cert.Status == "revoked" {
		return fmt.Errorf("certificate %s is already revoked", certID)
	}

	// 更新证书状态
	cert.Status = "revoked"
	cert.Metadata.RevocationReason = reason

	certBytes, err := json.Marshal(cert)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(certID, certBytes)
}

// GetCert 查询证书
func (s *SkillChaincode) GetCert(ctx contractapi.TransactionContextInterface, certID string) (*SkillCertificate, error) {
	log.Printf("查询证书: %s", certID)

	certBytes, err := ctx.GetStub().GetState(certID)
	if err != nil {
		return nil, fmt.Errorf("failed to read certificate %s: %v", certID, err)
	}
	if certBytes == nil {
		return nil, fmt.Errorf("certificate %s does not exist", certID)
	}

	var cert SkillCertificate
	err = json.Unmarshal(certBytes, &cert)
	if err != nil {
		return nil, err
	}

	return &cert, nil
}

// CertExists 检查证书是否存在
func (s *SkillChaincode) CertExists(ctx contractapi.TransactionContextInterface, certID string) (bool, error) {
	certBytes, err := ctx.GetStub().GetState(certID)
	if err != nil {
		return false, fmt.Errorf("failed to read certificate %s: %v", certID, err)
	}

	return certBytes != nil, nil
}

// GetAllCerts 获取所有证书
func (s *SkillChaincode) GetAllCerts(ctx contractapi.TransactionContextInterface) ([]*SkillCertificate, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var certs []*SkillCertificate
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var cert SkillCertificate
		err = json.Unmarshal(queryResponse.Value, &cert)
		if err != nil {
			continue
		}

		certs = append(certs, &cert)
	}

	return certs, nil
}

// GetCertsByHolder 根据持有者查询证书
func (s *SkillChaincode) GetCertsByHolder(ctx contractapi.TransactionContextInterface, holderDID string) ([]*SkillCertificate, error) {
	// 使用富查询（需要CouchDB）
	queryString := fmt.Sprintf(`{
		"selector": {
			"holderDid": "%s",
			"status": "active"
		}
	}`, holderDID)

	return s.getCertsFromQuery(ctx, queryString)
}

// GetCertsBySkill 根据技能名称查询证书
func (s *SkillChaincode) GetCertsBySkill(ctx contractapi.TransactionContextInterface, skillName string) ([]*SkillCertificate, error) {
	queryString := fmt.Sprintf(`{
		"selector": {
			"skillName": "%s",
			"status": "active"
		}
	}`, skillName)

	return s.getCertsFromQuery(ctx, queryString)
}

// getCertsFromQuery 执行查询并返回结果
func (s *SkillChaincode) getCertsFromQuery(ctx contractapi.TransactionContextInterface, queryString string) ([]*SkillCertificate, error) {
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var certs []*SkillCertificate
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var cert SkillCertificate
		err = json.Unmarshal(queryResponse.Value, &cert)
		if err != nil {
			continue
		}

		certs = append(certs, &cert)
	}

	return certs, nil
}

// CreateCertificationRequest 创建认证请求
func (s *SkillChaincode) CreateCertificationRequest(ctx contractapi.TransactionContextInterface, requestJSON string) (string, error) {
	log.Printf("创建认证请求: %s", requestJSON)

	var request CertificationRequest
	err := json.Unmarshal([]byte(requestJSON), &request)
	if err != nil {
		return "", fmt.Errorf("invalid request JSON: %v", err)
	}

	// 生成请求ID
	request.RequestID = fmt.Sprintf("req_%d", time.Now().UnixNano())
	request.Status = "pending"
	request.RequestDate = time.Now().Format(time.RFC3339)

	// 存储请求
	requestBytes, err := json.Marshal(request)
	if err != nil {
		return "", err
	}

	err = ctx.GetStub().PutState(request.RequestID, requestBytes)
	if err != nil {
		return "", err
	}

	return request.RequestID, nil
}

// ApproveCertificationRequest 批准认证请求
func (s *SkillChaincode) ApproveCertificationRequest(ctx contractapi.TransactionContextInterface, requestID string, issuerDID string) error {
	request, err := s.GetCertificationRequest(ctx, requestID)
	if err != nil {
		return err
	}

	if request.Status != "pending" {
		return fmt.Errorf("request %s is not in pending status", requestID)
	}

	// 更新请求状态
	request.Status = "approved"
	request.IssuerDID = issuerDID
	request.ReviewComments = "认证请求已批准"

	requestBytes, err := json.Marshal(request)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(requestID, requestBytes)
	if err != nil {
		return err
	}

	// 自动颁发证书
	cert := SkillCertificate{
		ID:             fmt.Sprintf("cert_%s", request.RequestID),
		HolderDID:      request.HolderDID,
		IssuerDID:      issuerDID,
		CredentialType: "SkillCertificate",
		SkillName:      request.SkillName,
		SkillLevel:     request.SkillLevel,
		IssueDate:      time.Now().Format(time.RFC3339),
		ExpiryDate:     time.Now().AddDate(2, 0, 0).Format(time.RFC3339),
		Evidence:       request.Evidence,
		Status:         "active",
		Metadata: VCProof{
			Type:               "Ed25519Signature2020",
			Created:            time.Now().Format(time.RFC3339),
			VerificationMethod: fmt.Sprintf("%s#keys-1", issuerDID),
			ProofPurpose:       "assertionMethod",
			Jws:                "auto-generated-signature",
		},
	}

	certBytes, err := json.Marshal(cert)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(cert.ID, certBytes)
}

// RejectCertificationRequest 拒绝认证请求
func (s *SkillChaincode) RejectCertificationRequest(ctx contractapi.TransactionContextInterface, requestID string, comments string) error {
	request, err := s.GetCertificationRequest(ctx, requestID)
	if err != nil {
		return err
	}

	if request.Status != "pending" {
		return fmt.Errorf("request %s is not in pending status", requestID)
	}

	// 更新请求状态
	request.Status = "rejected"
	request.ReviewComments = comments

	requestBytes, err := json.Marshal(request)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(requestID, requestBytes)
}

// GetCertificationRequest 获取认证请求
func (s *SkillChaincode) GetCertificationRequest(ctx contractapi.TransactionContextInterface, requestID string) (*CertificationRequest, error) {
	requestBytes, err := ctx.GetStub().GetState(requestID)
	if err != nil {
		return nil, fmt.Errorf("failed to read request %s: %v", requestID, err)
	}
	if requestBytes == nil {
		return nil, fmt.Errorf("request %s does not exist", requestID)
	}

	var request CertificationRequest
	err = json.Unmarshal(requestBytes, &request)
	if err != nil {
		return nil, err
	}

	return &request, nil
}

// GetPendingRequests 获取待处理的认证请求
func (s *SkillChaincode) GetPendingRequests(ctx contractapi.TransactionContextInterface) ([]*CertificationRequest, error) {
	queryString := `{
		"selector": {
			"status": "pending"
		}
	}`

	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var requests []*CertificationRequest
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var request CertificationRequest
		err = json.Unmarshal(queryResponse.Value, &request)
		if err != nil {
			continue
		}

		requests = append(requests, &request)
	}

	return requests, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SkillChaincode{})
	if err != nil {
		log.Panicf("Error creating skill chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting skill chaincode: %v", err)
	}
}