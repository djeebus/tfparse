// Copyright The Cloud Custodian Authors.
// SPDX-License-Identifier: Apache-2.0
package converter

type TerraformConverterOptions interface {
	SetDebug()
	SetStopOnHCLError()
}

type TerraformConverterOption func(t TerraformConverterOptions)

// WithDebug specifies an io.Writer for debug logs - if not set, they are discarded
func WithDebug() TerraformConverterOption {
	return func(t TerraformConverterOptions) {
		t.SetDebug()
	}
}

// WithStopOnHCLError sets the underlying defsec parser to error and stop on HCL parsing errors.
func WithStopOnHCLError() TerraformConverterOption {
	return func(t TerraformConverterOptions) {
		t.SetStopOnHCLError()
	}
}
